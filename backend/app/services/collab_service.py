"""Collaborative trip planning service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlmodel import delete, select

from ..db.database import session_scope
from ..db.models import (
    CollabTrip,
    CollabTripChange,
    CollabTripComment,
    CollabTripInvite,
    CollabTripMember,
    CollabTripVote,
    TripHistory,
    User,
)
from ..models.schemas import (
    CollabTripChangeData,
    CollabTripCommentData,
    CollabTripCommentCreateRequest,
    CollabTripCreateRequest,
    CollabTripDetailData,
    CollabTripInviteData,
    CollabTripInviteRequest,
    CollabTripMemberData,
    CollabTripSummaryData,
    CollabTripUpdateRequest,
    CollabTripVoteData,
    CollabTripVoteRequest,
    CollabUserData,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CollabService:
    editable_roles = {"owner", "editor"}
    admin_roles = {"owner"}

    def create_trip(self, user_id: str, payload: CollabTripCreateRequest) -> CollabTripDetailData:
        with session_scope() as session:
            track = session.exec(
                select(TripHistory)
                .where(TripHistory.id == payload.source_track_id)
                .where(TripHistory.user_id == user_id)
            ).first()
            if track is None:
                raise ValueError("Travel track was not found")
            if not track.plan_json:
                raise ValueError("This travel track has no saved plan")

            title = payload.title.strip() or f"{track.city} 协同行程"
            trip = CollabTrip(
                owner_user_id=user_id,
                source_track_id=track.id,
                title=title,
                city=track.city,
                start_date=track.start_date,
                end_date=track.end_date,
                plan_json=dict(track.plan_json or {}),
                status="draft",
                version=1,
                updated_at=_utcnow(),
            )
            session.add(trip)
            session.commit()
            session.refresh(trip)
            trip_id = trip.id

            member = CollabTripMember(trip_id=trip_id, user_id=user_id, role="owner", status="active")
            change = CollabTripChange(
                trip_id=trip_id,
                user_id=user_id,
                change_type="create",
                summary="创建了协同行程",
                before_json={},
                after_json=dict(trip.plan_json or {}),
            )
            session.add(member)
            session.add(change)
            session.commit()

        detail = self.get_trip_detail(user_id, trip_id)
        if detail is None:
            raise ValueError("Failed to create collaborative trip")
        return detail

    def list_trips(self, user_id: str) -> Tuple[List[CollabTripSummaryData], List[CollabTripInviteData]]:
        with session_scope() as session:
            memberships = session.exec(
                select(CollabTripMember)
                .where(CollabTripMember.user_id == user_id)
                .where(CollabTripMember.status == "active")
            ).all()
            trip_ids = [item.trip_id for item in memberships]
            trips = session.exec(select(CollabTrip).where(CollabTrip.id.in_(trip_ids))).all() if trip_ids else []
            all_members = session.exec(select(CollabTripMember).where(CollabTripMember.trip_id.in_(trip_ids))).all() if trip_ids else []
            comments = session.exec(select(CollabTripComment).where(CollabTripComment.trip_id.in_(trip_ids))).all() if trip_ids else []
            pending_invites = session.exec(
                select(CollabTripInvite)
                .where(CollabTripInvite.invitee_user_id == user_id)
                .where(CollabTripInvite.status == "pending")
                .order_by(CollabTripInvite.created_at.desc())
            ).all()
            invite_trip_ids = [item.trip_id for item in pending_invites]
            invite_trips = session.exec(select(CollabTrip).where(CollabTrip.id.in_(invite_trip_ids))).all() if invite_trip_ids else []
            user_ids = (
                [trip.owner_user_id for trip in trips]
                + [item.inviter_user_id for item in pending_invites]
                + [item.invitee_user_id for item in pending_invites]
            )
            users = session.exec(select(User).where(User.id.in_(list(dict.fromkeys([item for item in user_ids if item]))))).all() if user_ids else []

        role_by_trip_id = {item.trip_id: item.role for item in memberships}
        member_count_by_trip_id: Dict[str, int] = {}
        for item in all_members:
            if item.status == "active":
                member_count_by_trip_id[item.trip_id] = member_count_by_trip_id.get(item.trip_id, 0) + 1
        comment_count_by_trip_id: Dict[str, int] = {}
        for item in comments:
            comment_count_by_trip_id[item.trip_id] = comment_count_by_trip_id.get(item.trip_id, 0) + 1
        user_map = {user.id: user for user in users}
        invite_trip_map = {trip.id: trip for trip in invite_trips}

        return (
            [
                self._trip_summary(
                    trip=trip,
                    owner=self._user_data(user_map.get(trip.owner_user_id)),
                    my_role=role_by_trip_id.get(trip.id, "viewer"),
                    member_count=member_count_by_trip_id.get(trip.id, 0),
                    comment_count=comment_count_by_trip_id.get(trip.id, 0),
                )
                for trip in sorted(trips, key=lambda item: item.updated_at, reverse=True)
            ],
            [self._invite_data(item, user_map=user_map, trip=invite_trip_map.get(item.trip_id)) for item in pending_invites],
        )

    def get_trip_detail(self, user_id: str, trip_id: str) -> Optional[CollabTripDetailData]:
        with session_scope() as session:
            trip = session.get(CollabTrip, trip_id)
            if trip is None:
                return None
            my_member = self._get_active_member(session, trip_id, user_id)
            if my_member is None:
                return None

            members = session.exec(select(CollabTripMember).where(CollabTripMember.trip_id == trip_id)).all()
            invites = session.exec(
                select(CollabTripInvite)
                .where(CollabTripInvite.trip_id == trip_id)
                .order_by(CollabTripInvite.created_at.desc())
            ).all()
            comments = session.exec(
                select(CollabTripComment)
                .where(CollabTripComment.trip_id == trip_id)
                .order_by(CollabTripComment.created_at.desc())
            ).all()
            votes = session.exec(select(CollabTripVote).where(CollabTripVote.trip_id == trip_id)).all()
            changes = session.exec(
                select(CollabTripChange)
                .where(CollabTripChange.trip_id == trip_id)
                .order_by(CollabTripChange.created_at.desc())
                .limit(40)
            ).all()
            user_ids = (
                [trip.owner_user_id]
                + [item.user_id for item in members]
                + [item.inviter_user_id for item in invites]
                + [item.invitee_user_id for item in invites]
                + [item.user_id for item in comments]
                + [item.user_id for item in votes]
                + [item.user_id for item in changes]
            )
            users = session.exec(select(User).where(User.id.in_(list(dict.fromkeys([item for item in user_ids if item]))))).all()

        user_map = {user.id: user for user in users}
        return CollabTripDetailData(
            **self._trip_summary(
                trip=trip,
                owner=self._user_data(user_map.get(trip.owner_user_id)),
                my_role=my_member.role,
                member_count=len([item for item in members if item.status == "active"]),
                comment_count=len(comments),
            ).model_dump(),
            plan_json=dict(trip.plan_json or {}),
            members=[self._member_data(item, user_map) for item in members],
            invites=[self._invite_data(item, user_map=user_map, trip=trip) for item in invites],
            comments=[self._comment_data(item, user_map) for item in comments],
            votes=[self._vote_data(item, user_map) for item in votes],
            changes=[self._change_data(item, user_map) for item in changes],
        )

    def update_plan(self, user_id: str, trip_id: str, payload: CollabTripUpdateRequest) -> CollabTripDetailData:
        if not payload.plan_json:
            raise ValueError("Plan content cannot be empty")

        with session_scope() as session:
            trip = session.get(CollabTrip, trip_id)
            if trip is None:
                raise ValueError("Collaborative trip was not found")
            member = self._get_active_member(session, trip_id, user_id)
            if member is None or member.role not in self.editable_roles:
                raise PermissionError("You do not have permission to edit this trip")

            before = dict(trip.plan_json or {})
            trip.plan_json = dict(payload.plan_json)
            trip.version += 1
            trip.updated_at = _utcnow()
            session.add(trip)
            session.add(
                CollabTripChange(
                    trip_id=trip.id,
                    user_id=user_id,
                    change_type="update_plan",
                    summary=payload.summary.strip() or "更新了协同行程",
                    before_json=before,
                    after_json=dict(payload.plan_json),
                )
            )
            session.commit()

        detail = self.get_trip_detail(user_id, trip_id)
        if detail is None:
            raise ValueError("Collaborative trip was not found")
        return detail

    def delete_or_leave_trip(self, user_id: str, trip_id: str) -> str:
        with session_scope() as session:
            trip = session.get(CollabTrip, trip_id)
            if trip is None:
                raise ValueError("Collaborative trip was not found")
            member = self._get_active_member(session, trip_id, user_id)
            if member is None:
                raise ValueError("Collaborative trip was not found")

            if member.role == "owner" or trip.owner_user_id == user_id:
                session.exec(delete(CollabTripVote).where(CollabTripVote.trip_id == trip_id))
                session.exec(delete(CollabTripComment).where(CollabTripComment.trip_id == trip_id))
                session.exec(delete(CollabTripChange).where(CollabTripChange.trip_id == trip_id))
                session.exec(delete(CollabTripInvite).where(CollabTripInvite.trip_id == trip_id))
                session.exec(delete(CollabTripMember).where(CollabTripMember.trip_id == trip_id))
                session.delete(trip)
                session.commit()
                return "deleted"

            member.status = "left"
            session.add(member)
            session.add(
                CollabTripChange(
                    trip_id=trip_id,
                    user_id=user_id,
                    change_type="leave",
                    summary="退出了协同行程",
                )
            )
            session.commit()
            return "left"

    def create_invite(self, user_id: str, trip_id: str, payload: CollabTripInviteRequest) -> CollabTripInviteData:
        role = payload.role if payload.role in {"editor", "viewer"} else "editor"
        identifier = payload.identifier.strip()
        if not identifier:
            raise ValueError("Invitee cannot be empty")

        with session_scope() as session:
            trip = session.get(CollabTrip, trip_id)
            if trip is None:
                raise ValueError("Collaborative trip was not found")
            member = self._get_active_member(session, trip_id, user_id)
            if member is None or member.role not in self.admin_roles:
                raise PermissionError("Only the owner can invite members")
            invitee = self._find_user(session, identifier)
            if invitee is None:
                raise ValueError("No user matched this email or nickname")
            if invitee.id == user_id:
                raise ValueError("You cannot invite yourself")
            existing_member = self._get_active_member(session, trip_id, invitee.id)
            if existing_member is not None:
                raise ValueError("This user is already a member")
            existing_invite = session.exec(
                select(CollabTripInvite)
                .where(CollabTripInvite.trip_id == trip_id)
                .where(CollabTripInvite.invitee_user_id == invitee.id)
                .where(CollabTripInvite.status == "pending")
            ).first()
            if existing_invite is not None:
                raise ValueError("This user already has a pending invite")

            invite = CollabTripInvite(
                trip_id=trip_id,
                inviter_user_id=user_id,
                invitee_user_id=invitee.id,
                invitee_email=invitee.email or "",
                role=role,
                status="pending",
            )
            session.add(invite)
            session.add(
                CollabTripChange(
                    trip_id=trip_id,
                    user_id=user_id,
                    change_type="invite",
                    summary=f"邀请 {invitee.nickname or invitee.email or '旅行者'} 加入协同行程",
                )
            )
            session.commit()
            session.refresh(invite)
            users = session.exec(select(User).where(User.id.in_([user_id, invitee.id]))).all()
            return self._invite_data(invite, user_map={user.id: user for user in users}, trip=trip)

    def respond_invite(self, user_id: str, invite_id: str, accepted: bool) -> CollabTripInviteData:
        with session_scope() as session:
            invite = session.get(CollabTripInvite, invite_id)
            if invite is None or invite.invitee_user_id != user_id:
                raise ValueError("Invite was not found")
            if invite.status != "pending":
                raise ValueError("Invite has already been handled")
            trip = session.get(CollabTrip, invite.trip_id)
            if trip is None:
                raise ValueError("Collaborative trip was not found")
            invite.status = "accepted" if accepted else "rejected"
            invite.responded_at = _utcnow()
            session.add(invite)
            if accepted:
                session.add(
                    CollabTripMember(
                        trip_id=invite.trip_id,
                        user_id=user_id,
                        role=invite.role,
                        status="active",
                    )
                )
            session.add(
                CollabTripChange(
                    trip_id=invite.trip_id,
                    user_id=user_id,
                    change_type="accept_invite" if accepted else "reject_invite",
                    summary="接受了协同行程邀请" if accepted else "拒绝了协同行程邀请",
                )
            )
            session.commit()
            session.refresh(invite)
            users = session.exec(select(User).where(User.id.in_([invite.inviter_user_id, user_id]))).all()
            return self._invite_data(invite, user_map={user.id: user for user in users}, trip=trip)

    def add_comment(self, user_id: str, trip_id: str, payload: CollabTripCommentCreateRequest) -> CollabTripCommentData:
        content = payload.content.strip()
        if not content:
            raise ValueError("Comment content cannot be empty")

        with session_scope() as session:
            trip = session.get(CollabTrip, trip_id)
            member = self._get_active_member(session, trip_id, user_id)
            if trip is None or member is None:
                raise ValueError("Collaborative trip was not found")
            comment = CollabTripComment(
                trip_id=trip_id,
                day_index=payload.day_index,
                user_id=user_id,
                content=content[:500],
            )
            trip.updated_at = _utcnow()
            session.add(comment)
            session.add(trip)
            session.commit()
            session.refresh(comment)
            user = session.get(User, user_id)
            return self._comment_data(comment, {user_id: user} if user is not None else {})

    def toggle_vote(self, user_id: str, trip_id: str, payload: CollabTripVoteRequest) -> Tuple[CollabTripVoteData, bool]:
        with session_scope() as session:
            trip = session.get(CollabTrip, trip_id)
            member = self._get_active_member(session, trip_id, user_id)
            if trip is None or member is None:
                raise ValueError("Collaborative trip was not found")
            existing = session.exec(
                select(CollabTripVote)
                .where(CollabTripVote.trip_id == trip_id)
                .where(CollabTripVote.user_id == user_id)
                .where(CollabTripVote.target_type == payload.target_type)
                .where(CollabTripVote.target_id == payload.target_id)
                .where(CollabTripVote.vote_type == payload.vote_type)
            ).first()
            if existing is not None:
                user = session.get(User, user_id)
                vote_data = self._vote_data(existing, {user_id: user} if user is not None else {})
                session.delete(existing)
                session.commit()
                return vote_data, False
            vote = CollabTripVote(
                trip_id=trip_id,
                target_type=payload.target_type,
                target_id=payload.target_id,
                user_id=user_id,
                vote_type=payload.vote_type,
            )
            session.add(vote)
            session.commit()
            session.refresh(vote)
            user = session.get(User, user_id)
            return self._vote_data(vote, {user_id: user} if user is not None else {}), True

    @staticmethod
    def _get_active_member(session, trip_id: str, user_id: str) -> Optional[CollabTripMember]:
        return session.exec(
            select(CollabTripMember)
            .where(CollabTripMember.trip_id == trip_id)
            .where(CollabTripMember.user_id == user_id)
            .where(CollabTripMember.status == "active")
        ).first()

    @staticmethod
    def _find_user(session, identifier: str) -> Optional[User]:
        normalized = identifier.strip().lower()
        exact = session.exec(select(User).where(User.email == normalized)).first()
        if exact is not None:
            return exact
        exact_name = session.exec(select(User).where(User.nickname == identifier.strip())).first()
        if exact_name is not None:
            return exact_name
        return session.exec(select(User).where(User.nickname.ilike(f"%{identifier.strip()}%"))).first()

    @staticmethod
    def _user_data(user: Optional[User]) -> CollabUserData:
        if user is None:
            return CollabUserData(id="", nickname="旅行者")
        return CollabUserData(
            id=user.id,
            nickname=user.nickname or "旅行者",
            email=user.email or "",
            avatar_url=user.avatar_url or "",
        )

    @classmethod
    def _trip_summary(
        cls,
        trip: CollabTrip,
        owner: CollabUserData,
        my_role: str,
        member_count: int,
        comment_count: int,
    ) -> CollabTripSummaryData:
        return CollabTripSummaryData(
            id=trip.id,
            owner_user_id=trip.owner_user_id,
            source_track_id=trip.source_track_id,
            title=trip.title,
            city=trip.city,
            start_date=trip.start_date,
            end_date=trip.end_date,
            status=trip.status,
            version=trip.version,
            updated_at=trip.updated_at,
            created_at=trip.created_at,
            owner=owner,
            my_role=my_role,
            member_count=member_count,
            comment_count=comment_count,
        )

    @classmethod
    def _member_data(cls, member: CollabTripMember, user_map: Dict[str, User]) -> CollabTripMemberData:
        return CollabTripMemberData(
            id=member.id,
            trip_id=member.trip_id,
            user_id=member.user_id,
            role=member.role,
            status=member.status,
            joined_at=member.joined_at,
            user=cls._user_data(user_map.get(member.user_id)),
        )

    @classmethod
    def _invite_data(
        cls,
        invite: CollabTripInvite,
        user_map: Dict[str, User],
        trip: Optional[CollabTrip],
    ) -> CollabTripInviteData:
        return CollabTripInviteData(
            id=invite.id,
            trip_id=invite.trip_id,
            inviter_user_id=invite.inviter_user_id,
            invitee_user_id=invite.invitee_user_id,
            invitee_email=invite.invitee_email,
            role=invite.role,
            status=invite.status,
            created_at=invite.created_at,
            responded_at=invite.responded_at,
            inviter=cls._user_data(user_map.get(invite.inviter_user_id)),
            invitee=cls._user_data(user_map.get(invite.invitee_user_id)),
            trip_title=trip.title if trip is not None else "",
            city=trip.city if trip is not None else "",
        )

    @classmethod
    def _comment_data(cls, comment: CollabTripComment, user_map: Dict[str, User]) -> CollabTripCommentData:
        return CollabTripCommentData(
            id=comment.id,
            trip_id=comment.trip_id,
            day_index=comment.day_index,
            user_id=comment.user_id,
            content=comment.content,
            created_at=comment.created_at,
            user=cls._user_data(user_map.get(comment.user_id)),
        )

    @classmethod
    def _vote_data(cls, vote: CollabTripVote, user_map: Dict[str, User]) -> CollabTripVoteData:
        return CollabTripVoteData(
            id=vote.id,
            trip_id=vote.trip_id,
            target_type=vote.target_type,
            target_id=vote.target_id,
            user_id=vote.user_id,
            vote_type=vote.vote_type,
            created_at=vote.created_at,
            user=cls._user_data(user_map.get(vote.user_id)),
        )

    @classmethod
    def _change_data(cls, change: CollabTripChange, user_map: Dict[str, User]) -> CollabTripChangeData:
        return CollabTripChangeData(
            id=change.id,
            trip_id=change.trip_id,
            user_id=change.user_id,
            change_type=change.change_type,
            summary=change.summary,
            before_json=dict(change.before_json or {}),
            after_json=dict(change.after_json or {}),
            created_at=change.created_at,
            user=cls._user_data(user_map.get(change.user_id)),
        )


_collab_service: CollabService | None = None


def get_collab_service() -> CollabService:
    global _collab_service
    if _collab_service is None:
        _collab_service = CollabService()
    return _collab_service

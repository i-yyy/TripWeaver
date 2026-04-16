"""Personalized community travel feed service."""

from __future__ import annotations

import imghdr
import hashlib
import math
from pathlib import Path
from uuid import uuid4
from dataclasses import dataclass
from typing import Dict, List, Optional

from fastapi import UploadFile
from sqlmodel import select

from ..config import get_settings
from ..db.database import session_scope
from ..db.models import (
    CommunityComment,
    CommunityFollow,
    CommunityInteraction,
    CommunityPost,
    CommunityPostComment,
    CommunityPostLike,
    CommunityTripCardRecord,
    TripHistory,
    User,
    UserFeedback,
)
from ..models.schemas import (
    CommunityCommentData,
    CommunityFeedData,
    CommunityPostCommentData,
    CommunityPostCreateRequest,
    CommunityPostData,
    CommunityProfileHomeData,
    CommunityTripCard,
    CommunityUserSummary,
    FeedbackCreateRequest,
)
from .feedback_service import get_feedback_service
from .profile_service import get_profile_service


@dataclass(frozen=True)
class CommunitySeedCard:
    id: str
    city: str
    title: str
    subtitle: str
    summary: str
    cover_image_url: str
    days: int
    estimated_budget: str
    tags: List[str]
    travel_style: List[str]
    companions: List[str]
    highlights: List[str]
    author_name: str
    like_count: int
    favorite_count: int
    comment_count: int
    reuse_count: int
    source_type: str = "curated"


SEED_CARDS: List[CommunitySeedCard] = [
    CommunitySeedCard(
        id="community-hangzhou-citywalk",
        city="杭州",
        title="西湖边的轻量城市漫游",
        subtitle="适合第一次来杭州，也适合想慢慢走的人",
        summary="把西湖、茶馆、老街和傍晚湖岸串在同一天，节奏轻，拍照和休息点都比较充足。",
        cover_image_url="https://images.unsplash.com/photo-1598751337485-0d57b0c50b7a?auto=format&fit=crop&w=1200&q=80",
        days=2,
        estimated_budget="medium",
        tags=["citywalk", "culture", "tea", "photo_friendly", "slow"],
        travel_style=["citywalk", "slow", "local"],
        companions=["solo", "couple", "friends"],
        highlights=["西湖湖岸散步", "龙井茶体验", "傍晚城市夜色"],
        author_name="阿禾",
        like_count=328,
        favorite_count=146,
        comment_count=42,
        reuse_count=89,
    ),
    CommunitySeedCard(
        id="community-beijing-family-rain",
        city="北京",
        title="雨天也稳的亲子博物馆路线",
        subtitle="室内为主，适合家庭和低强度出行",
        summary="上午看展，午餐放在馆区周边，下午用科技馆或书店补充，减少下雨天反复折返。",
        cover_image_url="https://images.unsplash.com/photo-1599571234909-29ed5d1321d6?auto=format&fit=crop&w=1200&q=80",
        days=2,
        estimated_budget="medium",
        tags=["family", "museum", "rainy_day", "indoor", "less_walking"],
        travel_style=["museum", "slow"],
        companions=["family"],
        highlights=["博物馆主线", "室内备选", "亲子低步行"],
        author_name="小鹿一家",
        like_count=421,
        favorite_count=205,
        comment_count=58,
        reuse_count=132,
    ),
    CommunitySeedCard(
        id="community-shanghai-food-night",
        city="上海",
        title="外滩夜景和街区美食短途",
        subtitle="朋友或情侣都适合的一晚一日路线",
        summary="白天把历史街区和咖啡馆串联，晚上留给外滩夜景和本地小吃，适合轻社交出行。",
        cover_image_url="https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?auto=format&fit=crop&w=1200&q=80",
        days=2,
        estimated_budget="medium",
        tags=["food", "night", "citywalk", "local_flavor", "photo_friendly"],
        travel_style=["citywalk", "local"],
        companions=["couple", "friends"],
        highlights=["外滩夜景", "街区小吃", "咖啡馆停留"],
        author_name="周末在路上",
        like_count=386,
        favorite_count=178,
        comment_count=46,
        reuse_count=104,
    ),
    CommunitySeedCard(
        id="community-chengdu-slow-food",
        city="成都",
        title="慢节奏吃喝和公园茶馆",
        subtitle="给想放松的人留一点空白",
        summary="用人民公园、老街、小吃和晚间散步构成松弛路线，不追求高密度打卡。",
        cover_image_url="https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80",
        days=3,
        estimated_budget="medium",
        tags=["food", "slow", "local_flavor", "tea", "citywalk"],
        travel_style=["slow", "local", "citywalk"],
        companions=["solo", "couple", "friends"],
        highlights=["茶馆休息", "本地小吃", "慢节奏街区"],
        author_name="慢慢走",
        like_count=512,
        favorite_count=236,
        comment_count=73,
        reuse_count=158,
    ),
    CommunitySeedCard(
        id="community-xian-history-weekend",
        city="西安",
        title="两天历史文化主线",
        subtitle="适合喜欢历史和经典打卡的人",
        summary="把博物馆、古城墙和夜间街区放在一条清晰主线上，减少跨城折返。",
        cover_image_url="https://images.unsplash.com/photo-1580428180098-24b353d7e9d9?auto=format&fit=crop&w=1200&q=80",
        days=2,
        estimated_budget="medium",
        tags=["history", "culture", "museum", "night", "classic"],
        travel_style=["museum", "checkin", "citywalk"],
        companions=["solo", "couple", "family", "friends"],
        highlights=["博物馆主线", "古城墙", "夜间街区"],
        author_name="城墙边散步",
        like_count=467,
        favorite_count=221,
        comment_count=69,
        reuse_count=141,
    ),
    CommunitySeedCard(
        id="community-guangzhou-budget-food",
        city="广州",
        title="地铁友好的早茶和老城路线",
        subtitle="预算友好，吃得丰富，移动成本低",
        summary="围绕地铁可达片区安排早茶、骑楼街和老城散步，适合低预算也想吃好的用户。",
        cover_image_url="https://images.unsplash.com/photo-1519181245277-cffeb31da2e3?auto=format&fit=crop&w=1200&q=80",
        days=2,
        estimated_budget="low",
        tags=["food", "budget", "public_transit", "local_flavor", "citywalk"],
        travel_style=["local", "citywalk"],
        companions=["solo", "friends", "family"],
        highlights=["早茶体验", "骑楼街", "地铁串联"],
        author_name="陈记路线簿",
        like_count=299,
        favorite_count=131,
        comment_count=37,
        reuse_count=84,
    ),
    CommunitySeedCard(
        id="community-qingdao-seaside-family",
        city="青岛",
        title="海边轻松家庭短途",
        subtitle="海岸散步、亲子停留和低强度路线",
        summary="把海边栈道、公园和餐饮点放在同一片区，适合家庭慢慢玩，不把行程排得太满。",
        cover_image_url="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        days=3,
        estimated_budget="medium",
        tags=["family", "nature", "seaside", "less_walking", "slow"],
        travel_style=["slow", "local"],
        companions=["family", "couple"],
        highlights=["海岸散步", "亲子停留", "海鲜餐饮"],
        author_name="海风计划",
        like_count=274,
        favorite_count=126,
        comment_count=31,
        reuse_count=76,
    ),
    CommunitySeedCard(
        id="community-chongqing-night-city",
        city="重庆",
        title="山城夜景和本地风味",
        subtitle="适合朋友结伴的夜间路线",
        summary="白天降低爬坡强度，傍晚后进入江景、老街和本地餐饮场景，体验感更集中。",
        cover_image_url="https://images.unsplash.com/photo-1518005020951-eccb494ad742?auto=format&fit=crop&w=1200&q=80",
        days=3,
        estimated_budget="medium",
        tags=["night", "food", "local_flavor", "friends", "citywalk"],
        travel_style=["local", "citywalk"],
        companions=["friends", "couple"],
        highlights=["山城夜景", "本地火锅", "江边散步"],
        author_name="雾都夜行",
        like_count=489,
        favorite_count=243,
        comment_count=81,
        reuse_count=166,
    ),
]


TAG_ALIASES: Dict[str, str] = {
    "history": "history",
    "文化": "culture",
    "culture": "culture",
    "nature": "nature",
    "自然": "nature",
    "food": "food",
    "美食": "food",
    "museum": "museum",
    "博物馆": "museum",
    "shopping": "shopping",
    "citywalk": "citywalk",
    "slow": "slow",
    "慢节奏": "slow",
    "local": "local_flavor",
    "family": "family",
    "亲子": "family",
    "friends": "friends",
    "couple": "couple",
    "less_walking": "less_walking",
    "wheelchair": "less_walking",
    "rest_friendly": "slow",
    "public transit": "public_transit",
    "public_transit": "public_transit",
    "budget hotel": "budget",
    "low": "budget",
}


class CommunityService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.upload_dir) / "community"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_seed_cards()

    @staticmethod
    def _user_avatar_map(user_ids: List[str]) -> Dict[str, str]:
        normalized_ids = [user_id for user_id in user_ids if user_id]
        if not normalized_ids:
            return {}
        unique_ids = list(dict.fromkeys(normalized_ids))
        with session_scope() as session:
            users = session.exec(select(User).where(User.id.in_(unique_ids))).all()
        return {user.id: user.avatar_url or "" for user in users}

    @staticmethod
    def _seed_record_id(seed_id: str) -> str:
        return seed_id

    def _ensure_seed_cards(self) -> None:
        with session_scope() as session:
            for seed_card in SEED_CARDS:
                record_id = self._seed_record_id(seed_card.id)
                existing = session.get(CommunityTripCardRecord, record_id)
                if existing is not None:
                    continue
                session.add(
                    CommunityTripCardRecord(
                        id=record_id,
                        source_type="curated",
                        source_ref_id=seed_card.id,
                        author_name=seed_card.author_name,
                        city=seed_card.city,
                        title=seed_card.title,
                        subtitle=seed_card.subtitle,
                        summary=seed_card.summary,
                        cover_image_url=seed_card.cover_image_url,
                        days=seed_card.days,
                        estimated_budget=seed_card.estimated_budget,
                        tags=list(seed_card.tags),
                        travel_style=list(seed_card.travel_style),
                        companions=list(seed_card.companions),
                        highlights=list(seed_card.highlights),
                        like_count=seed_card.like_count,
                        favorite_count=seed_card.favorite_count,
                        comment_count=seed_card.comment_count,
                        reuse_count=seed_card.reuse_count,
                    )
                )
            session.commit()

    @staticmethod
    def _record_to_card(record: CommunityTripCardRecord) -> CommunitySeedCard:
        return CommunitySeedCard(
            id=record.id,
            city=record.city,
            title=record.title,
            subtitle=record.subtitle,
            summary=record.summary,
            cover_image_url=record.cover_image_url,
            days=record.days,
            estimated_budget=record.estimated_budget,
            tags=list(record.tags or []),
            travel_style=list(record.travel_style or []),
            companions=list(record.companions or []),
            highlights=list(record.highlights or []),
            author_name=record.author_name,
            like_count=record.like_count,
            favorite_count=record.favorite_count,
            comment_count=record.comment_count,
            reuse_count=record.reuse_count,
            source_type=record.source_type,
        )

    def _candidate_cards(self) -> List[CommunitySeedCard]:
        with session_scope() as session:
            records = session.exec(
                select(CommunityTripCardRecord)
                .where(CommunityTripCardRecord.status == "published")
                .order_by(CommunityTripCardRecord.updated_at.desc())
                .limit(300)
            ).all()
        if not records:
            return list(SEED_CARDS)
        return [self._record_to_card(record) for record in records]

    def build_feed(self, user_id: str, limit: int = 8, refresh_token: str = "") -> CommunityFeedData:
        preference_scores = self._profile_preference_scores(user_id)
        recent_cities = self._recent_cities(user_id)
        feedback_tags = self._feedback_tags(user_id)
        interaction_stats = self._interaction_stats(user_id)
        comments_by_card = self._recent_comments_by_card()

        candidate_cards = self._candidate_cards()
        recalled_cards = self._two_tower_recall(candidate_cards, preference_scores, recent_cities, feedback_tags, limit=max(limit * 4, 24))
        scored_cards = []
        for card, recall_score in recalled_cards:
            score, reasons = self._xdeepfm_rerank(card, recall_score, preference_scores, recent_cities, feedback_tags)
            if refresh_token:
                score += self._refresh_exploration_bonus(user_id, card.id, refresh_token)
                reasons = ["刷新推荐时加入少量探索重排", *reasons]
            stats = interaction_stats.get(card.id, {})
            scored_cards.append(
                CommunityTripCard(
                    id=card.id,
                    city=card.city,
                    title=card.title,
                    subtitle=card.subtitle,
                    summary=card.summary,
                    cover_image_url=card.cover_image_url,
                    days=card.days,
                    estimated_budget=card.estimated_budget,
                    tags=card.tags,
                    travel_style=card.travel_style,
                    companions=card.companions,
                    highlights=card.highlights,
                    author_name=card.author_name,
                    like_count=card.like_count + int(stats.get("like_count", 0)),
                    favorite_count=card.favorite_count + int(stats.get("favorite_count", 0)),
                    comment_count=card.comment_count,
                    reuse_count=card.reuse_count + int(stats.get("reuse_count", 0)),
                    match_score=round(score, 3),
                    match_reasons=reasons,
                    liked_by_me=bool(stats.get("liked_by_me", False)),
                    favorited_by_me=bool(stats.get("favorited_by_me", False)),
                    recent_comments=comments_by_card.get(card.id, []),
                )
            )

        cards = sorted(scored_cards, key=lambda item: item.match_score, reverse=True)[: max(1, limit)]
        preference_tags = [
            tag
            for tag, _score in sorted(preference_scores.items(), key=lambda kv: kv[1], reverse=True)[:6]
        ]
        if not preference_tags and feedback_tags:
            preference_tags = feedback_tags[:6]

        summary = self._build_summary(preference_tags, recent_cities)
        return CommunityFeedData(
            cards=cards,
            preference_tags=preference_tags,
            recent_cities=recent_cities[:5],
            summary=summary,
        )

    def toggle_interaction(self, user_id: str, card_id: str, interaction_type: str) -> bool:
        if interaction_type not in {"like", "favorite"}:
            raise ValueError("Unsupported community interaction")

        card = self._card_by_id(card_id)
        if card is None:
            raise ValueError("Community card not found")

        with session_scope() as session:
            statement = (
                select(CommunityInteraction)
                .where(CommunityInteraction.user_id == user_id)
                .where(CommunityInteraction.card_id == card_id)
                .where(CommunityInteraction.interaction_type == interaction_type)
            )
            interaction = session.exec(statement).first()
            if interaction is None:
                interaction = CommunityInteraction(
                    user_id=user_id,
                    card_id=card_id,
                    interaction_type=interaction_type,
                    active=True,
                    interaction_metadata=self._card_metadata(card),
                )
            else:
                interaction.active = not interaction.active
                interaction.interaction_metadata = self._card_metadata(card)

            session.add(interaction)
            session.commit()
            active = bool(interaction.active)

        if active:
            self._record_feedback_signal(user_id, card, interaction_type)
        return active

    def record_reuse(self, user_id: str, card_id: str) -> None:
        card = self._card_by_id(card_id)
        if card is None:
            raise ValueError("Community card not found")

        with session_scope() as session:
            interaction = CommunityInteraction(
                user_id=user_id,
                card_id=card_id,
                interaction_type="reuse",
                active=True,
                interaction_metadata=self._card_metadata(card),
            )
            session.add(interaction)
            session.commit()
        self._record_feedback_signal(user_id, card, "reuse")

    def add_comment(
        self,
        user_id: str,
        author_name: str,
        card_id: str,
        content: str,
    ) -> CommunityCommentData:
        card = self._card_by_id(card_id)
        if card is None:
            raise ValueError("Community card not found")

        text = content.strip()
        if not text:
            raise ValueError("Comment content cannot be empty")

        with session_scope() as session:
            comment = CommunityComment(
                user_id=user_id,
                card_id=card_id,
                author_name=author_name or "旅行者",
                content=text[:300],
            )
            session.add(comment)
            session.commit()
            session.refresh(comment)

        self._record_feedback_signal(user_id, card, "comment")
        return CommunityCommentData(
            id=comment.id,
            card_id=comment.card_id,
            author_name=comment.author_name,
            author_avatar_url=self._user_avatar_map([comment.user_id]).get(comment.user_id, ""),
            content=comment.content,
            created_at=comment.created_at,
        )

    def list_posts(self, user_id: str, limit: int = 20) -> List[CommunityPostData]:
        with session_scope() as session:
            posts = session.exec(
                select(CommunityPost)
                .where(CommunityPost.status == "published")
                .order_by(CommunityPost.created_at.desc())
                .limit(limit)
            ).all()
            likes = session.exec(
                select(CommunityPostLike).where(CommunityPostLike.user_id == user_id)
            ).all()
            follows = session.exec(
                select(CommunityFollow).where(CommunityFollow.follower_user_id == user_id)
            ).all()
            comments = session.exec(
                select(CommunityPostComment).order_by(CommunityPostComment.created_at.desc()).limit(200)
            ).all()

        liked_post_ids = {item.post_id for item in likes}
        followed_user_ids = {item.followed_user_id for item in follows}
        avatar_map = self._user_avatar_map(
            [post.user_id for post in posts] + [comment.user_id for comment in comments]
        )
        comments_by_post: Dict[str, List[CommunityPostCommentData]] = {}
        for comment in comments:
            items = comments_by_post.setdefault(comment.post_id, [])
            if len(items) >= 3:
                continue
            items.append(
                CommunityPostCommentData(
                    id=comment.id,
                    post_id=comment.post_id,
                    author_name=comment.author_name,
                    author_avatar_url=avatar_map.get(comment.user_id, ""),
                    content=comment.content,
                    created_at=comment.created_at,
                )
            )

        return [
            CommunityPostData(
                id=post.id,
                user_id=post.user_id,
                author_name=post.author_name,
                author_avatar_url=avatar_map.get(post.user_id, ""),
                content=post.content,
                image_urls=list(post.image_urls or []),
                city=post.city,
                tags=list(post.tags or []),
                linked_track_id=post.linked_track_id,
                linked_track_title=post.linked_track_title,
                like_count=post.like_count,
                comment_count=post.comment_count,
                created_at=post.created_at,
                liked_by_me=post.id in liked_post_ids,
                followed_author=post.user_id in followed_user_ids,
                recent_comments=comments_by_post.get(post.id, []),
            )
            for post in posts
        ]

    def get_profile_home(self, viewer_user_id: str, profile_user_id: str, limit: int = 60) -> Optional[CommunityProfileHomeData]:
        with session_scope() as session:
            profile_user = session.get(User, profile_user_id)
            if profile_user is None:
                return None

            posts = session.exec(
                select(CommunityPost)
                .where(CommunityPost.user_id == profile_user_id)
                .where(CommunityPost.status == "published")
                .order_by(CommunityPost.created_at.desc())
                .limit(limit)
            ).all()
            likes = session.exec(
                select(CommunityPostLike).where(CommunityPostLike.user_id == viewer_user_id)
            ).all()
            viewer_follows = session.exec(
                select(CommunityFollow).where(CommunityFollow.follower_user_id == viewer_user_id)
            ).all()
            followers = session.exec(
                select(CommunityFollow).where(CommunityFollow.followed_user_id == profile_user_id)
            ).all()
            following = session.exec(
                select(CommunityFollow).where(CommunityFollow.follower_user_id == profile_user_id)
            ).all()
            comments = session.exec(
                select(CommunityPostComment).order_by(CommunityPostComment.created_at.desc()).limit(300)
            ).all()
            related_user_ids = (
                [profile_user_id]
                + [item.follower_user_id for item in followers]
                + [item.followed_user_id for item in following]
                + [post.user_id for post in posts]
                + [comment.user_id for comment in comments]
            )
            users = session.exec(select(User).where(User.id.in_(list(dict.fromkeys(related_user_ids))))).all()

        user_map = {user.id: user for user in users}
        liked_post_ids = {item.post_id for item in likes}
        viewer_followed_user_ids = {item.followed_user_id for item in viewer_follows}
        avatar_map = {user.id: user.avatar_url or "" for user in users}
        comments_by_post: Dict[str, List[CommunityPostCommentData]] = {}
        visible_post_ids = {post.id for post in posts}
        for comment in comments:
            if comment.post_id not in visible_post_ids:
                continue
            items = comments_by_post.setdefault(comment.post_id, [])
            if len(items) >= 3:
                continue
            items.append(
                CommunityPostCommentData(
                    id=comment.id,
                    post_id=comment.post_id,
                    author_name=comment.author_name,
                    author_avatar_url=avatar_map.get(comment.user_id, ""),
                    content=comment.content,
                    created_at=comment.created_at,
                )
            )

        def user_summary(user_id: str) -> CommunityUserSummary:
            user = user_map.get(user_id)
            if user is None:
                return CommunityUserSummary(id=user_id, nickname="旅行者")
            return CommunityUserSummary(
                id=user.id,
                nickname=user.nickname or "旅行者",
                email=(user.email or "") if viewer_user_id == user.id else "",
                avatar_url=user.avatar_url or "",
                gender=user.gender or "",
                followed_by_me=user.id in viewer_followed_user_ids,
            )

        return CommunityProfileHomeData(
            user=user_summary(profile_user_id),
            follower_count=len(followers),
            following_count=len(following),
            post_count=len(posts),
            followers=[user_summary(item.follower_user_id) for item in followers],
            following=[user_summary(item.followed_user_id) for item in following],
            posts=[
                CommunityPostData(
                    id=post.id,
                    user_id=post.user_id,
                    author_name=post.author_name,
                    author_avatar_url=avatar_map.get(post.user_id, ""),
                    content=post.content,
                    image_urls=list(post.image_urls or []),
                    city=post.city,
                    tags=list(post.tags or []),
                    linked_track_id=post.linked_track_id,
                    linked_track_title=post.linked_track_title,
                    like_count=post.like_count,
                    comment_count=post.comment_count,
                    created_at=post.created_at,
                    liked_by_me=post.id in liked_post_ids,
                    followed_author=post.user_id in viewer_followed_user_ids,
                    recent_comments=comments_by_post.get(post.id, []),
                )
                for post in posts
            ],
        )

    def create_post(self, user_id: str, author_name: str, payload: CommunityPostCreateRequest) -> CommunityPostData:
        content = payload.content.strip()
        image_urls = [url.strip() for url in payload.image_urls if str(url).strip()][:9]
        tags = [tag.strip() for tag in payload.tags if str(tag).strip()][:8]
        linked_track_id = payload.linked_track_id.strip()
        linked_track_title = payload.linked_track_title.strip()
        if linked_track_id:
            with session_scope() as session:
                linked_track = session.exec(
                    select(TripHistory)
                    .where(TripHistory.id == linked_track_id)
                    .where(TripHistory.user_id == user_id)
                ).first()
                if linked_track is None:
                    raise ValueError("Linked trip plan not found")
                linked_track_title = linked_track_title or f"{linked_track.city} {linked_track.start_date} - {linked_track.end_date}"

        with session_scope() as session:
            post = CommunityPost(
                user_id=user_id,
                author_name=author_name or "旅行者",
                content=content,
                image_urls=image_urls,
                city=payload.city.strip(),
                tags=tags,
                linked_track_id=linked_track_id,
                linked_track_title=linked_track_title,
            )
            session.add(post)
            session.commit()
            session.refresh(post)

        self._upsert_post_trip_card(post)

        return CommunityPostData(
            id=post.id,
            user_id=post.user_id,
            author_name=post.author_name,
            author_avatar_url=self._user_avatar_map([post.user_id]).get(post.user_id, ""),
            content=post.content,
            image_urls=list(post.image_urls or []),
            city=post.city,
            tags=list(post.tags or []),
            linked_track_id=post.linked_track_id,
            linked_track_title=post.linked_track_title,
            like_count=post.like_count,
            comment_count=post.comment_count,
            created_at=post.created_at,
            liked_by_me=False,
            followed_author=False,
            recent_comments=[],
        )

    def toggle_post_like(self, user_id: str, post_id: str) -> bool:
        with session_scope() as session:
            post = session.get(CommunityPost, post_id)
            if post is None or post.status != "published":
                raise ValueError("Community post not found")

            statement = (
                select(CommunityPostLike)
                .where(CommunityPostLike.post_id == post_id)
                .where(CommunityPostLike.user_id == user_id)
            )
            existing = session.exec(statement).first()
            if existing is None:
                session.add(CommunityPostLike(post_id=post_id, user_id=user_id))
                post.like_count += 1
                active = True
            else:
                session.delete(existing)
                post.like_count = max(0, post.like_count - 1)
                active = False
            session.add(post)
            session.commit()

        if active:
            self._record_post_feedback_signal(user_id, post, "like")
            self._sync_post_trip_card_metrics(post)
        return active

    def add_post_comment(
        self,
        user_id: str,
        author_name: str,
        post_id: str,
        content: str,
    ) -> CommunityPostCommentData:
        text = content.strip()
        if not text:
            raise ValueError("Comment content cannot be empty")

        with session_scope() as session:
            post = session.get(CommunityPost, post_id)
            if post is None or post.status != "published":
                raise ValueError("Community post not found")

            comment = CommunityPostComment(
                post_id=post_id,
                user_id=user_id,
                author_name=author_name or "旅行者",
                content=text[:300],
            )
            post.comment_count += 1
            session.add(comment)
            session.add(post)
            session.commit()
            session.refresh(comment)

        self._record_post_feedback_signal(user_id, post, "comment")
        self._sync_post_trip_card_metrics(post)
        return CommunityPostCommentData(
            id=comment.id,
            post_id=comment.post_id,
            author_name=comment.author_name,
            author_avatar_url=self._user_avatar_map([comment.user_id]).get(comment.user_id, ""),
            content=comment.content,
            created_at=comment.created_at,
        )

    def toggle_follow(self, follower_user_id: str, followed_user_id: str) -> bool:
        if follower_user_id == followed_user_id:
            raise ValueError("You cannot follow yourself")

        with session_scope() as session:
            statement = (
                select(CommunityFollow)
                .where(CommunityFollow.follower_user_id == follower_user_id)
                .where(CommunityFollow.followed_user_id == followed_user_id)
            )
            existing = session.exec(statement).first()
            if existing is None:
                session.add(
                    CommunityFollow(
                        follower_user_id=follower_user_id,
                        followed_user_id=followed_user_id,
                    )
                )
                session.commit()
                return True
            session.delete(existing)
            session.commit()
            return False

    @staticmethod
    def get_post_linked_plan(post_id: str) -> Optional[Dict[str, object]]:
        with session_scope() as session:
            post = session.get(CommunityPost, post_id)
            if post is None or post.status != "published" or not post.linked_track_id:
                return None
            track = session.get(TripHistory, post.linked_track_id)
            if track is None:
                return None
            return dict(track.plan_json or {})

    def save_uploaded_image(self, file: UploadFile) -> str:
        content_type = (file.content_type or "").lower()
        if not content_type.startswith("image/"):
            raise ValueError("Only image files are supported")

        data = file.file.read()
        if not data:
            raise ValueError("Uploaded image is empty")
        if len(data) > 8 * 1024 * 1024:
            raise ValueError("Image must be smaller than 8MB")

        detected_type = imghdr.what(None, data)
        extension_map = {
            "jpeg": ".jpg",
            "png": ".png",
            "gif": ".gif",
            "webp": ".webp",
            "bmp": ".bmp",
        }
        extension = extension_map.get(str(detected_type or "").lower())
        if extension is None:
            raise ValueError("Unsupported image format")

        filename = f"{uuid4().hex}{extension}"
        target_path = self.upload_dir / filename
        target_path.write_bytes(data)
        return f"/uploads/community/{filename}"

    @staticmethod
    def _upsert_post_trip_card(post: CommunityPost) -> None:
        if not (post.city or post.tags or post.image_urls):
            return

        image_urls = list(post.image_urls or [])
        tags = list(post.tags or [])
        title_city = post.city or "社区"
        content = (post.content or "").strip()
        title = content[:28] if content else f"{title_city}旅行动态"
        if len(content) > 28:
            title = f"{title}..."
        subtitle = content[:48] if content else "来自社区用户的真实旅行分享"
        if len(content) > 48:
            subtitle = f"{subtitle}..."

        with session_scope() as session:
            record_id = f"post-{post.id}"
            record = session.get(CommunityTripCardRecord, record_id)
            if record is None:
                record = CommunityTripCardRecord(
                    id=record_id,
                    source_type="ugc_post",
                    source_ref_id=post.id,
                )
            record.author_user_id = post.user_id
            record.author_name = post.author_name or "旅行者"
            record.city = post.city or ""
            record.title = title
            record.subtitle = subtitle
            record.summary = content or subtitle
            record.cover_image_url = image_urls[0] if image_urls else ""
            record.days = 1
            record.estimated_budget = "medium"
            record.tags = tags
            record.travel_style = tags
            record.companions = []
            record.highlights = [item for item in [post.city, *tags[:3]] if item]
            if post.linked_track_id and post.linked_track_title:
                record.highlights = [post.linked_track_title, *record.highlights][:4]
            record.like_count = post.like_count
            record.comment_count = post.comment_count
            record.status = post.status
            record.updated_at = post.created_at
            session.add(record)
            session.commit()

    @staticmethod
    def _sync_post_trip_card_metrics(post: CommunityPost) -> None:
        with session_scope() as session:
            record = session.get(CommunityTripCardRecord, f"post-{post.id}")
            if record is None:
                return
            record.like_count = post.like_count
            record.comment_count = post.comment_count
            record.updated_at = post.created_at
            session.add(record)
            session.commit()

    def _profile_preference_scores(self, user_id: str) -> Dict[str, float]:
        profile = get_profile_service().get_profile_data(user_id)
        scores: Dict[str, float] = {}
        if profile is None:
            return scores

        for raw_tag, value in (profile.interest_weights or {}).items():
            tag = self._normalize_tag(raw_tag)
            if not tag:
                continue
            scores[tag] = max(scores.get(tag, 0.0), float(value or 0.0))

        for raw_tag in profile.mobility_needs or []:
            tag = self._normalize_tag(raw_tag)
            if tag:
                scores[tag] = max(scores.get(tag, 0.0), 0.72)

        if profile.budget_level == "low":
            scores["budget"] = max(scores.get("budget", 0.0), 0.8)
        if profile.preferred_transportation:
            transport_tag = self._normalize_tag(profile.preferred_transportation)
            if transport_tag:
                scores[transport_tag] = max(scores.get(transport_tag, 0.0), 0.68)

        return scores

    @staticmethod
    def _recent_cities(user_id: str) -> List[str]:
        with session_scope() as session:
            statement = (
                select(TripHistory.city)
                .where(TripHistory.user_id == user_id)
                .order_by(TripHistory.created_at.desc())
                .limit(8)
            )
            cities = session.exec(statement).all()
        unique_cities = []
        for city in cities:
            if city and city not in unique_cities:
                unique_cities.append(city)
        return unique_cities

    def _feedback_tags(self, user_id: str) -> List[str]:
        with session_scope() as session:
            statement = (
                select(UserFeedback)
                .where(UserFeedback.user_id == user_id)
                .where(UserFeedback.feedback_type.in_(["like", "satisfied"]))
                .order_by(UserFeedback.created_at.desc())
                .limit(12)
            )
            feedback_items = session.exec(statement).all()

        tags: List[str] = []
        for item in feedback_items:
            for raw_tag in [item.target_type, item.target_name, *list((item.feedback_metadata or {}).get("tags", []))]:
                tag = self._normalize_tag(raw_tag)
                if tag and tag not in tags:
                    tags.append(tag)
        return tags

    @staticmethod
    def _interaction_stats(user_id: str) -> Dict[str, Dict[str, object]]:
        with session_scope() as session:
            interactions = session.exec(
                select(CommunityInteraction).where(CommunityInteraction.active == True)  # noqa: E712
            ).all()

        stats: Dict[str, Dict[str, object]] = {}
        for item in interactions:
            card_stats = stats.setdefault(
                item.card_id,
                {
                    "like_count": 0,
                    "favorite_count": 0,
                    "reuse_count": 0,
                    "liked_by_me": False,
                    "favorited_by_me": False,
                },
            )
            if item.interaction_type == "like":
                card_stats["like_count"] = int(card_stats["like_count"]) + 1
                if item.user_id == user_id:
                    card_stats["liked_by_me"] = True
            elif item.interaction_type == "favorite":
                card_stats["favorite_count"] = int(card_stats["favorite_count"]) + 1
                if item.user_id == user_id:
                    card_stats["favorited_by_me"] = True
            elif item.interaction_type == "reuse":
                card_stats["reuse_count"] = int(card_stats["reuse_count"]) + 1
        return stats

    @staticmethod
    def _recent_comments_by_card() -> Dict[str, List[CommunityCommentData]]:
        with session_scope() as session:
            comments = session.exec(
                select(CommunityComment)
                .where(CommunityComment.status == "published")
                .order_by(CommunityComment.created_at.desc())
                .limit(120)
            ).all()

        avatar_map = CommunityService._user_avatar_map([comment.user_id for comment in comments])
        grouped: Dict[str, List[CommunityCommentData]] = {}
        for comment in comments:
            items = grouped.setdefault(comment.card_id, [])
            if len(items) >= 2:
                continue
            items.append(
                CommunityCommentData(
                    id=comment.id,
                    card_id=comment.card_id,
                    author_name=comment.author_name,
                    author_avatar_url=avatar_map.get(comment.user_id, ""),
                    content=comment.content,
                    created_at=comment.created_at,
                )
            )
        return grouped

    def _two_tower_recall(
        self,
        cards: List[CommunitySeedCard],
        preference_scores: Dict[str, float],
        recent_cities: List[str],
        feedback_tags: List[str],
        limit: int,
    ) -> List[tuple[CommunitySeedCard, float]]:
        user_vector = self._user_tower_vector(preference_scores, recent_cities, feedback_tags)
        scored: List[tuple[CommunitySeedCard, float]] = []
        for card in cards:
            card_vector = self._item_tower_vector(card)
            score = self._cosine_similarity(user_vector, card_vector)
            if card.city in recent_cities:
                score += 0.08
            if card.source_type in {"ugc_post", "saved_plan"}:
                score += 0.03
            scored.append((card, max(0.0, min(score, 1.0))))
        return sorted(scored, key=lambda item: item[1], reverse=True)[: max(1, limit)]

    def _xdeepfm_rerank(
        self,
        card: CommunitySeedCard,
        recall_score: float,
        preference_scores: Dict[str, float],
        recent_cities: List[str],
        feedback_tags: List[str],
    ) -> tuple[float, List[str]]:
        score = 0.26 + recall_score * 0.34
        reasons: List[str] = []
        card_tags = set(card.tags + card.travel_style + card.companions)
        matched_preferences = [tag for tag in card_tags if tag in preference_scores and preference_scores[tag] > 0]
        matched_feedback = [tag for tag in card_tags if tag in feedback_tags]

        if matched_preferences:
            preference_gain = sum(preference_scores[tag] for tag in matched_preferences[:4]) / max(1, len(matched_preferences[:4]))
            score += min(0.32, preference_gain * 0.28)
            reasons.append(f"匹配你的偏好：{'、'.join(matched_preferences[:3])}")

        if matched_feedback:
            score += min(0.16, 0.06 * len(matched_feedback))
            reasons.append(f"延续你近期喜欢的内容：{'、'.join(matched_feedback[:2])}")

        if card.city in recent_cities:
            score += 0.06
            reasons.append(f"你最近关注过 {card.city}")

        if "budget" in preference_scores and card.estimated_budget == "low":
            score += 0.12
            reasons.append("符合你的低预算倾向")

        explicit_cross = 0.0
        if matched_preferences and card.city in recent_cities:
            explicit_cross += 0.08
        if matched_preferences and matched_feedback:
            explicit_cross += 0.07
        if "family" in card_tags and "less_walking" in card_tags:
            explicit_cross += 0.03
        if "food" in card_tags and "local_flavor" in card_tags:
            explicit_cross += 0.03
        score += explicit_cross

        deep_component = min(0.1, 0.015 * len(card_tags) + 0.02 * len(matched_preferences))
        if card.source_type == "ugc_post":
            deep_component += 0.03
            reasons.append("来自社区真实旅行动态")
        score += deep_component

        popularity = min(0.12, (card.favorite_count + card.reuse_count) / 4000)
        score += popularity

        if not reasons:
            reasons.append("社区热度高，适合作为灵感起点")
        reasons.insert(0, f"Two-Tower召回相似度 {round(recall_score * 100)}%，xDeepFM已精排")
        return min(score, 0.98), reasons[:4]

    @staticmethod
    def _user_tower_vector(
        preference_scores: Dict[str, float],
        recent_cities: List[str],
        feedback_tags: List[str],
    ) -> Dict[str, float]:
        vector: Dict[str, float] = {}
        for tag, score in preference_scores.items():
            vector[f"tag:{tag}"] = vector.get(f"tag:{tag}", 0.0) + float(score or 0.0)
        for tag in feedback_tags:
            vector[f"tag:{tag}"] = vector.get(f"tag:{tag}", 0.0) + 0.8
        for city in recent_cities:
            vector[f"city:{city}"] = vector.get(f"city:{city}", 0.0) + 0.9
        if not vector:
            vector["global:popular"] = 1.0
        return vector

    @staticmethod
    def _item_tower_vector(card: CommunitySeedCard) -> Dict[str, float]:
        vector: Dict[str, float] = {f"city:{card.city}": 1.0, "global:popular": 0.35}
        for tag in list(card.tags) + list(card.travel_style) + list(card.companions):
            vector[f"tag:{tag}"] = vector.get(f"tag:{tag}", 0.0) + 1.0
        vector[f"budget:{card.estimated_budget}"] = 0.6
        vector[f"source:{card.source_type}"] = 0.5
        return vector

    @staticmethod
    def _cosine_similarity(left: Dict[str, float], right: Dict[str, float]) -> float:
        keys = set(left) | set(right)
        dot = sum(left.get(key, 0.0) * right.get(key, 0.0) for key in keys)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    @staticmethod
    def _refresh_exploration_bonus(user_id: str, card_id: str, refresh_token: str) -> float:
        digest = hashlib.sha256(f"{user_id}:{card_id}:{refresh_token}".encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) / 0xFFFFFFFF
        return bucket * 0.06

    def _score_card(
        self,
        card: CommunitySeedCard,
        preference_scores: Dict[str, float],
        recent_cities: List[str],
        feedback_tags: List[str],
    ) -> tuple[float, List[str]]:
        score = 0.42
        reasons: List[str] = []
        card_tags = set(card.tags + card.travel_style + card.companions)

        matched_preferences = [
            tag for tag in card_tags if tag in preference_scores and preference_scores[tag] > 0
        ]
        if matched_preferences:
            preference_gain = sum(preference_scores[tag] for tag in matched_preferences[:4]) / max(
                1,
                len(matched_preferences[:4]),
            )
            score += min(0.32, preference_gain * 0.28)
            reasons.append(f"匹配你的偏好：{'、'.join(matched_preferences[:3])}")

        matched_feedback = [tag for tag in card_tags if tag in feedback_tags]
        if matched_feedback:
            score += min(0.16, 0.06 * len(matched_feedback))
            reasons.append(f"延续你近期喜欢的内容：{'、'.join(matched_feedback[:2])}")

        if card.city in recent_cities:
            score += 0.06
            reasons.append(f"你最近关注过 {card.city}")

        if "budget" in preference_scores and card.estimated_budget == "low":
            score += 0.12
            reasons.append("符合你的低预算倾向")

        popularity = min(0.12, (card.favorite_count + card.reuse_count) / 4000)
        score += popularity

        if not reasons:
            reasons.append("社区热度高，适合作为灵感起点")

        return min(score, 0.98), reasons[:4]

    @staticmethod
    def _card_by_id(card_id: str) -> Optional[CommunitySeedCard]:
        with session_scope() as session:
            record = session.get(CommunityTripCardRecord, card_id)
        if record is not None:
            return CommunityService._record_to_card(record)
        return next((card for card in SEED_CARDS if card.id == card_id or card.id.replace("community-", "public-") == card_id), None)

    @staticmethod
    def _card_metadata(card: CommunitySeedCard) -> Dict[str, object]:
        return {
            "card_id": card.id,
            "city": card.city,
            "tags": card.tags,
            "travel_style": card.travel_style,
            "companions": card.companions,
            "estimated_budget": card.estimated_budget,
        }

    def _record_feedback_signal(self, user_id: str, card: CommunitySeedCard, interaction_type: str) -> None:
        try:
            get_feedback_service().create_feedback(
                FeedbackCreateRequest(
                    user_id=user_id,
                    session_id="community",
                    target_type="community_card",
                    target_name=card.title,
                    feedback_type="satisfied" if interaction_type in {"favorite", "reuse"} else "like",
                    reason=f"community_{interaction_type}",
                    metadata=self._card_metadata(card),
                )
            )
        except Exception:
            # Community interaction should not fail just because profile/memory enrichment failed.
            return

    @staticmethod
    def _record_post_feedback_signal(user_id: str, post: CommunityPost, interaction_type: str) -> None:
        try:
            get_feedback_service().create_feedback(
                FeedbackCreateRequest(
                    user_id=user_id,
                    session_id="community_post",
                    target_type="community_post",
                    target_name=post.city or post.author_name,
                    feedback_type="like",
                    reason=f"community_post_{interaction_type}",
                    metadata={
                        "city": post.city,
                        "tags": list(post.tags or []),
                        "post_id": post.id,
                    },
                )
            )
        except Exception:
            return

    @staticmethod
    def _normalize_tag(value: object) -> str:
        text = str(value or "").strip().lower()
        if not text:
            return ""
        if text in TAG_ALIASES:
            return TAG_ALIASES[text]
        for source, target in TAG_ALIASES.items():
            if source in text:
                return target
        return text

    @staticmethod
    def _build_summary(preference_tags: List[str], recent_cities: List[str]) -> str:
        if preference_tags and recent_cities:
            return f"已结合你的偏好标签 {', '.join(preference_tags[:3])} 和最近关注城市 {', '.join(recent_cities[:2])} 推荐社区路线。"
        if preference_tags:
            return f"已结合你的偏好标签 {', '.join(preference_tags[:4])} 推荐社区路线。"
        if recent_cities:
            return f"已结合你最近关注的 {', '.join(recent_cities[:3])} 推荐社区路线。"
        return "还没有足够画像数据，先为你展示社区里热度较高、复用率较高的路线。"


_community_service: Optional[CommunityService] = None


def get_community_service() -> CommunityService:
    global _community_service
    if _community_service is None:
        _community_service = CommunityService()
    return _community_service

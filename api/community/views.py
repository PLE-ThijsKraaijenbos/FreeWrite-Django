from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment, Post, Tag
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    PostCreateSerializer,
    PostSerializer,
    PostUpdateSerializer,
    TagSerializer,
)
from .services import CommentService, PostService


_POST_ID_PARAM = OpenApiParameter(
    name='post_id',
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="ID of the post.",
)

_COMMENT_ID_PARAM = OpenApiParameter(
    name='comment_id',
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="ID of the comment.",
)


@extend_schema_view(
    get=extend_schema(
        tags=['Community'],
        summary="List tags",
        description="Returns every tag that can be attached to a post. Not paginated, so the whole list comes back at once.",
        responses={200: TagSerializer(many=True)},
    ),
)
class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


@extend_schema_view(
    get=extend_schema(
        tags=['Community'],
        summary="List posts",
        description=(
            "Returns the community feed, newest first, paginated 20 per page. Each post is "
            "annotated for the current user with the like count, whether they liked it, whether "
            "they wrote it, and the author's display name."
        ),
        responses={200: PostSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Community'],
        summary="Create a post",
        description=(
            "Creates a post authored by the current user. Send it as `multipart/form-data` so an "
            "image file can be attached. Both the image and the tags are optional. If an image is "
            "sent it is uploaded to Cloudinary and the resulting URL is stored on the post."
        ),
        request=PostCreateSerializer,
        responses={201: PostCreateSerializer},
    ),
)
class PostListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        return PostService.get_post_list()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(APIView):
    @extend_schema(
        tags=['Community'],
        summary="Update a post",
        description=(
            "Updates a post. Only the author may do this. Send it as `multipart/form-data`. Every "
            "field is optional, so this works as a partial update: send only what changes. Sending "
            "an image replaces the existing one, and sending `tag_ids` replaces the whole set of tags."
        ),
        parameters=[_POST_ID_PARAM],
        request=PostUpdateSerializer,
        responses={
            200: OpenApiResponse(response=PostSerializer, description="Post updated. Returns the full post."),
            403: OpenApiResponse(
                description="The current user is not the author of this post.",
                examples=[OpenApiExample("Not the author", value={"detail": "You do not have permission to perform this action."})],
            ),
            404: OpenApiResponse(description="No post with this ID."),
        },
    )
    def patch(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        serializer = PostUpdateSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_post = serializer.save(user=request.user)
        return Response(PostSerializer(updated_post, context={'request': request}).data)

    @extend_schema(
        tags=['Community'],
        summary="Delete a post",
        description="Deletes a post. Only the author may do this.",
        parameters=[_POST_ID_PARAM],
        responses={
            204: OpenApiResponse(description="Post deleted. No body."),
            403: OpenApiResponse(
                description="The current user is not the author of this post.",
                examples=[OpenApiExample("Not the author", value={"detail": "You do not have permission to perform this action."})],
            ),
            404: OpenApiResponse(description="No post with this ID."),
        },
    )
    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        PostService.delete_post(post=post, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        tags=['Community'],
        summary="List comments",
        description="Returns the comments on a post, oldest first, paginated 20 per page. Each comment is annotated for the current user with the like count and whether they liked it.",
        parameters=[_POST_ID_PARAM],
        responses={200: CommentSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Community'],
        summary="Create a comment",
        description="Adds a comment to a post. Returns the full comment.",
        parameters=[_POST_ID_PARAM],
        request=CommentCreateSerializer,
        responses={
            201: OpenApiResponse(response=CommentSerializer, description="Comment created."),
            404: OpenApiResponse(description="No post with this ID."),
        },
    ),
)
class CommentListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        return CommentService.get_comment_list(post_id=self.kwargs['post_id'])

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer

    def create(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(post=post)
        return Response(
            CommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class CommentLikeView(APIView):
    @extend_schema(
        tags=['Community'],
        summary="Like a comment",
        description="Likes the comment for the current user. Idempotent: liking a comment you already liked is a no-op and still succeeds.",
        parameters=[_POST_ID_PARAM, _COMMENT_ID_PARAM],
        request=None,
        responses={
            200: OpenApiResponse(description="Comment liked, or already liked. No body."),
            404: OpenApiResponse(description="No comment with this ID on this post."),
        },
    )
    def post(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
        CommentService.like_comment(user=request.user, comment=comment)
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Community'],
        summary="Unlike a comment",
        description="Removes the current user's like from the comment. Safe to call even if there was no like.",
        parameters=[_POST_ID_PARAM, _COMMENT_ID_PARAM],
        responses={
            204: OpenApiResponse(description="Like removed. No body."),
            404: OpenApiResponse(description="No comment with this ID on this post."),
        },
    )
    def delete(self, request, post_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
        CommentService.unlike_comment(user=request.user, comment=comment)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostLikeView(APIView):
    @extend_schema(
        tags=['Community'],
        summary="Like a post",
        description="Likes the post for the current user. Idempotent: liking a post you already liked is a no-op and still succeeds.",
        parameters=[_POST_ID_PARAM],
        request=None,
        responses={
            200: OpenApiResponse(description="Post liked, or already liked. No body."),
            404: OpenApiResponse(description="No post with this ID."),
        },
    )
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        PostService.like_post(user=request.user, post=post)
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Community'],
        summary="Unlike a post",
        description="Removes the current user's like from the post. Safe to call even if there was no like.",
        parameters=[_POST_ID_PARAM],
        responses={
            204: OpenApiResponse(description="Like removed. No body."),
            404: OpenApiResponse(description="No post with this ID."),
        },
    )
    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        PostService.unlike_post(user=request.user, post=post)
        return Response(status=status.HTTP_204_NO_CONTENT)

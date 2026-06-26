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

from .models import Post, Tag
from .serializers import (
    PostCreateSerializer,
    PostSerializer,
    PostUpdateSerializer,
    TagSerializer,
)
from .services import PostService


_POST_ID_PARAM = OpenApiParameter(
    name='post_id',
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.INT,
    description="ID of the post.",
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

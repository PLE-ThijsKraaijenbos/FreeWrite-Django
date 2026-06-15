from django.shortcuts import get_object_or_404
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


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


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
    def patch(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        serializer = PostUpdateSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_post = serializer.save(user=request.user)
        return Response(PostSerializer(updated_post, context={'request': request}).data)

    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        PostService.delete_post(post=post, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostLikeView(APIView):
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        PostService.like_post(user=request.user, post=post)
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        PostService.unlike_post(user=request.user, post=post)
        return Response(status=status.HTTP_204_NO_CONTENT)

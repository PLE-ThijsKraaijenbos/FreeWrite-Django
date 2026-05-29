from rest_framework import generics

from .models import Post
from .serializers import PostSerializer


class PostListView(generics.ListAPIView):
    queryset = Post.objects.order_by('-id')
    serializer_class = PostSerializer

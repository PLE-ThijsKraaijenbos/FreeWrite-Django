import cloudinary.uploader
from rest_framework.exceptions import PermissionDenied

from .models import Post, PostLike


class PostService:
    @staticmethod
    def get_post_list():
        return Post.objects.order_by('-created_at')

    @staticmethod
    def create_post(*, author, title, body, image=None) -> Post:
        image_url = None
        if image:
            result = cloudinary.uploader.upload(image, folder='community/posts', resource_type='image')
            image_url = result['secure_url']
        return Post.objects.create(author=author, title=title, body=body, image_url=image_url)

    @staticmethod
    def update_post(*, post: Post, user, image=None, **fields) -> Post:
        if post.author != user:
            raise PermissionDenied()
        for attr, value in fields.items():
            setattr(post, attr, value)
        if image is not None:
            result = cloudinary.uploader.upload(image, folder='community/posts', resource_type='image')
            post.image_url = result['secure_url']
        post.save()
        return post

    @staticmethod
    def like_post(*, user, post: Post) -> None:
        PostLike.objects.get_or_create(user=user, post=post)

    @staticmethod
    def unlike_post(*, user, post: Post) -> None:
        PostLike.objects.filter(user=user, post=post).delete()

import cloudinary.uploader
from rest_framework.exceptions import PermissionDenied

from .models import Post, PostLike, Tag


class PostService:
    @staticmethod
    def get_post_list():
        return Post.objects.order_by('-created_at')

    @staticmethod
    def create_post(*, author, title, body, image=None, tag_ids=None) -> Post:
        image_url = None
        if image:
            result = cloudinary.uploader.upload(image, folder='community/posts', resource_type='image')
            image_url = result['secure_url']
        post = Post.objects.create(author=author, title=title, body=body, image_url=image_url)
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            post.tags.set(tags)
        return post

    @staticmethod
    def update_post(*, post: Post, user, image=None, tag_ids=None, **fields) -> Post:
        if post.author != user:
            raise PermissionDenied()
        for attr, value in fields.items():
            setattr(post, attr, value)
        if image is not None:
            result = cloudinary.uploader.upload(image, folder='community/posts', resource_type='image')
            post.image_url = result['secure_url']
        if tag_ids is not None:
            tags = Tag.objects.filter(id__in=tag_ids)
            post.tags.set(tags)
        post.save()
        return post

    @staticmethod
    def delete_post(*, post: Post, user) -> None:
        if post.author != user:
            raise PermissionDenied()
        post.delete()

    @staticmethod
    def like_post(*, user, post: Post) -> None:
        PostLike.objects.get_or_create(user=user, post=post)

    @staticmethod
    def unlike_post(*, user, post: Post) -> None:
        PostLike.objects.filter(user=user, post=post).delete()

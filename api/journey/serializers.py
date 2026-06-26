import json
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import (
    Journey, Phase, JourneyStep, JourneyStepProgress,
    JournalContent, LetterContent, ChoiceStoryContent,
    SpeechBubbleContent, BubblePopContent, ScaleContent,
)


class JournalContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalContent
        fields = ['id', 'title_text', 'input_field_placeholder']


class LetterContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterContent
        fields = ['id', 'title_text', 'greeting_placeholder']


class ChoiceStoryContentSerializer(serializers.ModelSerializer):
    story_content = serializers.SerializerMethodField()

    def get_story_content(self, obj):
        # Handle double-encoded JSON (stored as string instead of object)
        if isinstance(obj.story_content, str):
            return json.loads(obj.story_content)
        return obj.story_content

    class Meta:
        model = ChoiceStoryContent
        fields = ['id', 'title_text', 'story_content']


class SpeechBubbleContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechBubbleContent
        fields = ['id', 'title_text', 'bubbles']


class BubblePopContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BubblePopContent
        fields = ['id', 'title_text', 'thoughts']


class ScaleContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScaleContent
        fields = ['id', 'title_text', 'left_label', 'right_label']


_CONTENT_FIELD_MAP = {
    'journal': ('journal_content', JournalContentSerializer),
    'letter': ('letter_content', LetterContentSerializer),
    'choice_story': ('choice_story_content', ChoiceStoryContentSerializer),
    'speech_bubble': ('speech_bubble_content', SpeechBubbleContentSerializer),
    'bubble_pop': ('bubble_pop_content', BubblePopContentSerializer),
    'scale': ('scale_content', ScaleContentSerializer),
}


class PhaseNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = ['id', 'title', 'order']


class JourneyStepSerializer(serializers.ModelSerializer):
    phase = PhaseNestedSerializer(read_only=True)
    content = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_content(self, obj):
        entry = _CONTENT_FIELD_MAP.get(obj.assignment_type)
        if not entry:
            return None
        field_name, serializer_class = entry
        content_obj = getattr(obj, field_name, None)
        if content_obj is None:
            return None
        return serializer_class(content_obj).data

    class Meta:
        model = JourneyStep
        fields = ['id', 'title', 'description', 'banner_url', 'assignment_type', 'is_core', 'order', 'phase', 'content']


class JourneyStepProgressSerializer(serializers.ModelSerializer):
    step = JourneyStepSerializer(read_only=True)

    class Meta:
        model = JourneyStepProgress
        fields = ['id', 'step', 'status', 'bookmarked', 'started_at', 'completed_at', 'response_data']
        read_only_fields = ['started_at', 'completed_at']


class JourneySerializer(serializers.ModelSerializer):
    step_progresses = JourneyStepProgressSerializer(many=True, read_only=True)

    class Meta:
        model = Journey
        fields = ['id', 'step_progresses']


class CompleteStepRequestSerializer(serializers.Serializer):
    """Request body for completing a step."""

    response_data = serializers.JSONField(required=False)

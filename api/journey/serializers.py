from rest_framework import serializers
from .models import Journey, Phase, JourneyStep, JourneyStepProgress


class JourneyStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyStep
        fields = ['id', 'title', 'description', 'banner_url', 'assignment_type', 'is_core', 'order']


class PhaseSerializer(serializers.ModelSerializer):
    steps = JourneyStepSerializer(many=True, read_only=True)

    class Meta:
        model = Phase
        fields = ['id', 'title', 'order', 'steps']


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

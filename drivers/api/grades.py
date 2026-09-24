"""
API endpoints for managing driver grades and requirements.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db import transaction

from drivers.models import Grade, GradeRequirement, DriverGrade
from drivers.serializers import (
    GradeSerializer, 
    GradeRequirementSerializer,
    DriverGradeSerializer
)
from drivers.services.grade_service import GradeEvaluationService


# Grade Management Endpoints

@extend_schema(
    tags=['Grades Management'],
    description='List all available grades',
    responses={
        200: GradeSerializer(many=True),
        403: {"description": "Permission denied. Admin access required."}
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_grades(request: Request) -> Response:
    """
    List all available grades.
    """
    if not request.user.is_staff:
        return Response(
            {"detail": "You do not have permission to perform this action."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    grades = Grade.objects.all().order_by('commission_rate')
    serializer = GradeSerializer(grades, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=['Grades Management'],
    description='Create a new grade',
    request=GradeSerializer,
    responses={
        201: GradeSerializer,
        400: {"description": "Invalid data provided"},
        403: {"description": "Permission denied. Admin access required."}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_grade(request: Request) -> Response:
    """
    Create a new grade.
    """
    serializer = GradeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Grades Management'],
    description='Update a grade',
    request=GradeSerializer,
    responses={
        200: GradeSerializer,
        400: {"description": "Invalid data provided"},
        403: {"description": "Permission denied. Admin access required."},
        404: {"description": "Grade not found"}
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_grade(request: Request, grade_id: int) -> Response:
    """
    Update a grade.
    """
    try:
        grade = Grade.objects.get(id=grade_id)
    except Grade.DoesNotExist:
        return Response(
            {"detail": "Grade not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = GradeSerializer(grade, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Grades Management'],
    description='Delete a grade',
    responses={
        204: {"description": "Grade deleted successfully"},
        400: {"description": "Cannot delete grade with active drivers"},
        403: {"description": "Permission denied. Admin access required."},
        404: {"description": "Grade not found"}
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_grade(request: Request, grade_id: int) -> Response:
    """
    Delete a grade.
    """
    try:
        grade = Grade.objects.get(id=grade_id)
    except Grade.DoesNotExist:
        return Response(
            {"detail": "Grade not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if any driver is currently assigned to this grade
    if DriverGrade.objects.filter(grade=grade, is_current=True).exists():
        return Response(
            {"detail": "Cannot delete a grade that is currently assigned to drivers."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    grade.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Grade Requirement Management Endpoints

@extend_schema(
    tags=['Grade Requirements'],
    description='List all requirements for a grade',
    responses={
        200: GradeRequirementSerializer(many=True),
        403: {"description": "Permission denied. Admin access required."},
        404: {"description": "Grade not found"}
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_grade_requirements(request: Request, grade_id: int) -> Response:
    """
    List all requirements for a specific grade.
    """
    if not request.user.is_staff:
        return Response(
            {"detail": "You do not have permission to perform this action."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        grade = Grade.objects.get(id=grade_id)
    except Grade.DoesNotExist:
        return Response(
            {"detail": "Grade not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    requirements = grade.requirements.all()
    serializer = GradeRequirementSerializer(requirements, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=['Grade Requirements'],
    description='Add a requirement to a grade',
    request=GradeRequirementSerializer,
    responses={
        201: GradeRequirementSerializer,
        400: {"description": "Invalid data provided"},
        403: {"description": "Permission denied. Admin access required."},
        404: {"description": "Grade not found"}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def add_grade_requirement(request: Request, grade_id: int) -> Response:
    """
    Add a requirement to a grade.
    """
    try:
        grade = Grade.objects.get(id=grade_id)
    except Grade.DoesNotExist:
        return Response(
            {"detail": "Grade not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    data = request.data.copy()
    data['grade'] = grade.id
    
    serializer = GradeRequirementSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Grade Requirements'],
    description='Update a grade requirement',
    request=GradeRequirementSerializer,
    responses={
        200: GradeRequirementSerializer,
        400: {"description": "Invalid data provided"},
        403: {"description": "Permission denied. Admin access required."},
        404: {"description": "Requirement not found"}
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_grade_requirement(request: Request, requirement_id: int) -> Response:
    """
    Update a grade requirement.
    """
    try:
        requirement = GradeRequirement.objects.get(id=requirement_id)
    except GradeRequirement.DoesNotExist:
        return Response(
            {"detail": "Requirement not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = GradeRequirementSerializer(requirement, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Grade Requirements'],
    description='Delete a grade requirement',
    responses={
        204: {"description": "Requirement deleted successfully"},
        403: {"description": "Permission denied. Admin access required."},
        404: {"description": "Requirement not found"}
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_grade_requirement(request: Request, requirement_id: int) -> Response:
    """
    Delete a grade requirement.
    """
    try:
        requirement = GradeRequirement.objects.get(id=requirement_id)
    except GradeRequirement.DoesNotExist:
        return Response(
            {"detail": "Requirement not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    requirement.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Driver Grade Management Endpoints

@extend_schema(
    tags=['Driver Grades'],
    description="Get a driver's current grade",
    responses={
        200: DriverGradeSerializer,
        403: {"description": "Permission denied"},
        404: {"description": "Driver not found or has no grade"}
    },
    parameters=[
        OpenApiParameter(
            name='driver_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='ID of the driver',
            required=True
        )
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_driver_grade(request: Request, driver_id: str) -> Response:
    """
    Get a driver's current grade.
    """
    # Check if the requesting user has permission to view this driver's grade
    if not request.user.is_staff and str(request.user.id) != driver_id:
        return Response(
            {"detail": "You do not have permission to view this driver's grade."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        driver_grade = DriverGrade.objects.get(
            driver_id=driver_id,
            is_current=True
        )
    except DriverGrade.DoesNotExist:
        return Response(
            {"detail": "Driver has no active grade."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = DriverGradeSerializer(driver_grade)
    return Response(serializer.data)


@extend_schema(
    tags=['Driver Grades'],
    description="Update a driver's grade",
    request=DriverGradeSerializer,
    responses={
        200: DriverGradeSerializer,
        400: {"description": "Invalid data provided"},
        403: {"description": "Permission denied. Admin access required."},
        404: {"description": "Driver or grade not found"}
    },
    parameters=[
        OpenApiParameter(
            name='driver_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='ID of the driver',
            required=True
        )
    ]
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_driver_grade(request: Request, driver_id: str) -> Response:
    """
    Update a driver's grade (admin only).
    """
    try:
        grade_id = request.data.get('grade_id')
        if not grade_id:
            return Response(
                {"detail": "grade_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        grade = Grade.objects.get(id=grade_id)
        
        with transaction.atomic():
            # Update the driver's grade using the service
            success, message = GradeEvaluationService.update_driver_grade(
                driver_id=driver_id,
                new_grade=grade,
                reason=f"Grade manually updated by admin: {request.user.email}"
            )
            
            if not success:
                return Response(
                    {"detail": message},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the updated driver grade
            driver_grade = DriverGrade.objects.get(
                driver_id=driver_id,
                is_current=True
            )
            
            serializer = DriverGradeSerializer(driver_grade)
            return Response(serializer.data)
            
    except Grade.DoesNotExist:
        return Response(
            {"detail": "Grade not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    tags=['Driver Grades'],
    description="Get a driver's grade history",
    responses={
        200: DriverGradeSerializer(many=True),
        403: {"description": "Permission denied"},
        404: {"description": "Driver not found"}
    },
    parameters=[
        OpenApiParameter(
            name='driver_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='ID of the driver',
            required=True
        )
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_driver_grade_history(request: Request, driver_id: str) -> Response:
    """
    Get a driver's grade history.
    """
    # Check if the requesting user has permission to view this driver's grade history
    if not request.user.is_staff and str(request.user.id) != driver_id:
        return Response(
            {"detail": "You do not have permission to view this driver's grade history."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    grades = DriverGrade.objects.filter(
        driver_id=driver_id
    ).order_by('-assigned_at')
    
    if not grades.exists():
        return Response(
            {"detail": "No grade history found for this driver."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = DriverGradeSerializer(grades, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=['Driver Grades'],
    description="Force a driver's grade evaluation",
    responses={
        200: {"description": "Grade evaluation completed successfully"},
        400: {"description": "Evaluation failed"},
        403: {"description": "Permission denied. Admin access required."},
        404: {"description": "Driver not found"}
    },
    parameters=[
        OpenApiParameter(
            name='driver_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='ID of the driver',
            required=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def evaluate_driver_grade(request: Request, driver_id: str) -> Response:
    """
    Force a driver's grade evaluation (admin only).
    """
    try:
        from drivers.models import Drivers
        driver = Drivers.objects.get(id=driver_id)
        
        # Evaluate and update the driver's grade
        success, message = GradeEvaluationService.evaluate_and_update_driver_grade(driver)
        
        if not success:
            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the updated grade
        driver_grade = DriverGrade.objects.get(
            driver_id=driver_id,
            is_current=True
        )
        
        serializer = DriverGradeSerializer(driver_grade)
        return Response(serializer.data)
        
    except Drivers.DoesNotExist:
        return Response(
            {"detail": "Driver not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

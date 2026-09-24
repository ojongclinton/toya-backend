from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drivers.models import Grade
from ..customs import JWT
from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=['Backoffice - Grades'],
    request={
        'application/json': {
            'example': {
                'name': 'Bronze',
                'commission_rate': 12.00
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_grade(request):
    """Créer un nouveau grade"""
    _, user = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    name = request.data.get('name')
    commission_rate = request.data.get('commission_rate')
    
    if not name or commission_rate is None:
        return Response({
            "Message": "name and commission_rate are required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Vérifier si le nom existe déjà
    if Grade.objects.filter(name__iexact=name).exists():
        return Response({
            "Message": f"Grade '{name}' already exists"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    grade = Grade.objects.create(
        name=name,
        commission_rate=commission_rate,
        is_active=True
    )
    
    return Response({
        "Message": "Grade created successfully",
        "Data": {
            'id': str(grade.id),
            'name': grade.name,
            'commission_rate': float(grade.commission_rate)
        }
    }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Backoffice - Grades'],
    request={
        'application/json': {
            'example': {
                'commission_rate': 10.00,
                'is_active': True
            }
        }
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_grade(request, grade_id):
    """Modifier un grade existant"""
    _, user = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        grade = Grade.objects.get(id=grade_id)
    except Grade.DoesNotExist:
        return Response({
            "Message": "Grade not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Mise à jour
    if 'commission_rate' in request.data:
        grade.commission_rate = request.data['commission_rate']
    
    if 'is_active' in request.data:
        grade.is_active = request.data['is_active']
    
    if 'name' in request.data:
        grade.name = request.data['name']
    
    grade.save()
    
    return Response({
        "Message": "Grade updated successfully",
        "Data": {
            'id': str(grade.id),
            'name': grade.name,
            'commission_rate': float(grade.commission_rate),
            'is_active': grade.is_active
        }
    }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Backoffice - Grades'],
    responses={200: {'type': 'array', 'items': {'type': 'object'}}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_grades(request):
    """Liste tous les grades ACTIFS avec leurs taux de commission"""
    _, user = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    # FILTRER par is_active=True
    grades = Grade.objects.filter(is_active=True).order_by('commission_rate')
    
    data = [{
        'id': str(grade.id),
        'name': grade.name,
        'commission_rate': float(grade.commission_rate),
        'is_active': grade.is_active,
        'created_at': grade.created_at,
        'updated_at': grade.updated_at
    } for grade in grades]
    
    return Response({
        "Message": "Grades list",
        "Count": len(data),
        "Data": data
    }, status=status.HTTP_200_OK)
    
    
@extend_schema(
    tags=['Backoffice - Grades']
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_grade(request, grade_id):
    """Supprimer un grade (soft delete)"""
    _, user = JWT.filter_and_decode_token(request.headers.get("Authorization"))
    
    try:
        grade = Grade.objects.get(id=grade_id)
    except Grade.DoesNotExist:
        return Response({
            "Message": "Grade not found"
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Soft delete
    grade.is_active = False
    grade.save()
    
    return Response({
        "Message": f"Grade '{grade.name}' deactivated successfully"
    }, status=status.HTTP_200_OK)
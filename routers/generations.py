from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from typing import List
from routers.schemas import GenerationCreate, GenerationPublish, Generation
from services.generations_service import (
    get_user_generations, 
    create_generation, 
    get_generation_by_id, 
    update_generation_publish_status, 
    delete_generation
)
from routers.auth import get_current_user

router = APIRouter()

@router.get("/history", response_model=List[Generation])
async def get_generations_history(current_user = Depends(get_current_user)):
    """
    Получение истории генераций пользователя
    """
    user_id = current_user["id"]
    generations = get_user_generations(user_id)
    return generations

@router.post("", response_model=Generation)
async def add_generation(generation_data: GenerationCreate, current_user = Depends(get_current_user)):
    """
    Добавление новой генерации
    """
    user_id = current_user["id"]
    new_generation = create_generation(user_id, generation_data.title, generation_data.content)
    
    if not new_generation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create generation"
        )
    
    return new_generation

@router.put("/{id}/publish", response_model=Generation)
async def publish_generation(
    publish_data: GenerationPublish, 
    id: int = Path(..., title="Generation ID"),
    current_user = Depends(get_current_user)
):
    """
    Обновление статуса публикации
    """
    user_id = current_user["id"]
    generation = get_generation_by_id(id, user_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
    
    success = update_generation_publish_status(
        id, 
        user_id, 
        publish_data.published, 
        publish_data.publication_platform, 
        publish_data.social_network_url
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update publication status"
        )
    
    # Получаем обновленную генерацию
    updated_generation = get_generation_by_id(id, user_id)
    return updated_generation

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_generation(
    id: int = Path(..., title="Generation ID"),
    current_user = Depends(get_current_user)
):
    """
    Удаление записи из истории
    """
    user_id = current_user["id"]
    generation = get_generation_by_id(id, user_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation not found"
        )
    
    success = delete_generation(id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete generation"
        ) 
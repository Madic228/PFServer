from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from routers.schemas import GenerationCreate, GenerationPublish, Generation
from services.generations_service import (
    get_user_generations, 
    create_generation, 
    get_generation_by_id, 
    update_generation_publish_status, 
    delete_generation,
    update_generation
)
from routers.auth import get_current_user

router = APIRouter()

@router.get("/history", response_model=List[Generation])
async def get_generations_history(
    current_user = Depends(get_current_user)
):
    """
    Получение истории генераций текущего аутентифицированного пользователя.
    
    Идентификатор пользователя извлекается из JWT токена.
    Токен передается в заголовке Authorization: Bearer {token}
    """
    user_id = current_user["id"]
    generations = get_user_generations(user_id)
    return generations

@router.get("/{id}", response_model=Generation)
async def get_generation(
    id: int = Path(..., title="ID генерации", description="Уникальный идентификатор генерации"),
    current_user = Depends(get_current_user)
):
    """
    Получение конкретной генерации по ID.
    
    Пользователь может получить только свои генерации.
    ID пользователя извлекается из JWT токена.
    """
    user_id = current_user["id"]
    generation = get_generation_by_id(id, user_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Генерация не найдена или принадлежит другому пользователю"
        )
    
    return generation

@router.post("", response_model=Generation)
async def add_generation(
    generation_data: GenerationCreate, 
    current_user = Depends(get_current_user)
):
    """
    Добавление новой генерации для текущего пользователя.
    
    ID пользователя извлекается из JWT токена.
    Токен передается в заголовке Authorization: Bearer {token}
    """
    user_id = current_user["id"]
    new_generation = create_generation(user_id, generation_data.title, generation_data.content)
    
    if not new_generation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать генерацию"
        )
    
    return new_generation

@router.put("/{id}/publish", response_model=Generation)
async def publish_generation(
    publish_data: GenerationPublish, 
    id: int = Path(..., title="ID генерации", description="Уникальный идентификатор генерации"),
    current_user = Depends(get_current_user)
):
    """
    Обновление статуса публикации для конкретной генерации.
    
    Пользователь может обновлять только свои генерации.
    ID пользователя извлекается из JWT токена.
    """
    user_id = current_user["id"]
    generation = get_generation_by_id(id, user_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Генерация не найдена или принадлежит другому пользователю"
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
            detail="Не удалось обновить статус публикации"
        )
    
    # Получаем обновленную генерацию
    updated_generation = get_generation_by_id(id, user_id)
    return updated_generation

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_generation(
    id: int = Path(..., title="ID генерации", description="Уникальный идентификатор генерации"),
    current_user = Depends(get_current_user)
):
    """
    Удаление генерации по ID.
    
    Пользователь может удалять только свои генерации.
    ID пользователя извлекается из JWT токена.
    """
    user_id = current_user["id"]
    generation = get_generation_by_id(id, user_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Генерация не найдена или принадлежит другому пользователю"
        )
    
    success = delete_generation(id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить генерацию"
        )

@router.put("/{id}/edit", response_model=Generation)
async def edit_generation(
    generation_data: GenerationCreate,
    id: int = Path(..., title="ID генерации", description="Уникальный идентификатор генерации"),
    current_user = Depends(get_current_user)
):
    """
    Редактирование генерации пользователя.
    Пользователь может редактировать только свои генерации.
    ID пользователя извлекается из JWT токена.
    """
    user_id = current_user["id"]
    generation = get_generation_by_id(id, user_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Генерация не найдена или принадлежит другому пользователю"
        )
    
    success = update_generation(id, user_id, generation_data.title, generation_data.content)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить генерацию"
        )
    
    # Получаем обновленную генерацию
    updated_generation = get_generation_by_id(id, user_id)
    return updated_generation 
package usecase

import (
	"klar-api/internal/domain"
)

type ClickUpUseCase interface {
	CreateTask(listID string, task domain.CreateClickUpTaskRequest) (*domain.ClickUpTask, error)
	UpdateTask(taskID string, task domain.UpdateClickUpTaskRequest) error
	GetTaskDetails(taskID string) (*domain.ClickUpTask, error)
	AddComment(taskID string, comment string) error
	AssignTask(taskID string, userID int) error
}

type clickUpUseCase struct {
	repo domain.ClickUpRepository
}

func NewClickUpUseCase(repo domain.ClickUpRepository) ClickUpUseCase {
	return &clickUpUseCase{repo: repo}
}

func (u *clickUpUseCase) CreateTask(listID string, task domain.CreateClickUpTaskRequest) (*domain.ClickUpTask, error) {
	return u.repo.CreateTask(listID, task)
}

func (u *clickUpUseCase) UpdateTask(taskID string, task domain.UpdateClickUpTaskRequest) error {
	return u.repo.UpdateTask(taskID, task)
}

func (u *clickUpUseCase) GetTaskDetails(taskID string) (*domain.ClickUpTask, error) {
	return u.repo.GetTaskDetails(taskID)
}

func (u *clickUpUseCase) AddComment(taskID string, comment string) error {
	return u.repo.AddComment(taskID, comment)
}

func (u *clickUpUseCase) AssignTask(taskID string, userID int) error {
	return u.repo.AssignTask(taskID, userID)
}

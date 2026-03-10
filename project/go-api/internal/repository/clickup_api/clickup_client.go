package clickup_api

import (
	"fmt"
	"klar-api/internal/domain"
	"klar-api/pkg/logger"

	"github.com/go-resty/resty/v2"
)

type clickUpClient struct {
	logger *logger.Logger
	client *resty.Client
}

func NewClickUpClient(logger *logger.Logger, baseURL, apiKey string) domain.ClickUpRepository {
	client := resty.New().
		SetBaseURL(baseURL).
		SetHeader("Authorization", apiKey).
		SetHeader("Content-Type", "application/json")

	return &clickUpClient{
		logger: logger,
		client: client,
	}
}

func (c *clickUpClient) CreateTask(listID string, task domain.CreateClickUpTaskRequest) (*domain.ClickUpTask, error) {
	c.logger.Info("Creating task in list %s: %s", listID, task.Name)

	var result domain.ClickUpTask
	resp, err := c.client.R().
		SetBody(task).
		SetResult(&result).
		Post("/list/" + listID + "/task")

	if err != nil {
		c.logger.Error("Failed to create ClickUp task: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("ClickUp API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	c.logger.Info("Successfully created ClickUp task %s", result.ID)
	return &result, nil
}

func (c *clickUpClient) UpdateTask(taskID string, task domain.UpdateClickUpTaskRequest) error {
	c.logger.Info("Updating task %s", taskID)

	resp, err := c.client.R().
		SetBody(task).
		Put("/task/" + taskID)

	if err != nil {
		c.logger.Error("Failed to update ClickUp task: %v", err)
		return err
	}

	if resp.IsError() {
		c.logger.Error("ClickUp API error: %s", resp.String())
		return fmt.Errorf("%w: %s", domain.ErrExternalAPI, resp.String())
	}

	c.logger.Info("Successfully updated ClickUp task %s", taskID)
	return nil
}

func (c *clickUpClient) GetTaskDetails(taskID string) (*domain.ClickUpTask, error) {
	c.logger.Info("Fetching details for task %s", taskID)

	var result domain.ClickUpTask
	resp, err := c.client.R().
		SetResult(&result).
		Get("/task/" + taskID)

	if err != nil {
		c.logger.Error("Failed to fetch ClickUp task: %v", err)
		return nil, err
	}

	if resp.IsError() {
		c.logger.Error("ClickUp API error: %s", resp.String())
		return nil, domain.ErrExternalAPI
	}

	c.logger.Info("Successfully fetched ClickUp task %s", result.ID)
	return &result, nil
}

func (c *clickUpClient) AddComment(taskID string, comment string) error {
	c.logger.Info("Adding comment to task %s", taskID)

	resp, err := c.client.R().
		SetBody(map[string]string{"comment_text": comment}).
		Post("/task/" + taskID + "/comment")

	if err != nil {
		c.logger.Error("Failed to add ClickUp comment: %v", err)
		return err
	}

	if resp.IsError() {
		c.logger.Error("ClickUp API error: %s", resp.String())
		return domain.ErrExternalAPI
	}

	c.logger.Info("Successfully added comment to ClickUp task %s", taskID)
	return nil
}

func (c *clickUpClient) AssignTask(taskID string, userID int) error {
	c.logger.Info("Assigning task %s to user %d", taskID, userID)

	resp, err := c.client.R().
		SetBody(map[string]interface{}{
			"assignees": map[string]interface{}{
				"add": []int{userID},
			},
		}).
		Put("/task/" + taskID)

	if err != nil {
		c.logger.Error("Failed to assign ClickUp task: %v", err)
		return err
	}

	if resp.IsError() {
		c.logger.Error("ClickUp API error: %s", resp.String())
		return domain.ErrExternalAPI
	}

	c.logger.Info("Successfully assigned ClickUp task %s", taskID)
	return nil
}

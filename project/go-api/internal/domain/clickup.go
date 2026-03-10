package domain

type ClickUpTask struct {
	ID           string           `json:"id"`
	CustomID     *string          `json:"custom_id"`
	CustomItemID int              `json:"custom_item_id"`
	Name         string           `json:"name"`
	TextContent  string           `json:"text_content"`
	Description  string           `json:"description"`
	Status       *ClickUpStatus   `json:"status"`
	OrderIndex   string           `json:"orderindex"`
	DateCreated  string           `json:"date_created"`
	DateUpdated  string           `json:"date_updated"`
	DateClosed   *string          `json:"date_closed"`
	DateDone     *string          `json:"date_done"`
	Archived     bool             `json:"archived"`
	Creator      *ClickUpUser     `json:"creator"`
	Assignees    []ClickUpUser    `json:"assignees"`
	Watchers     []ClickUpUser    `json:"watchers"`
	TeamID       string           `json:"team_id"`
	URL          string           `json:"url"`
	Permission   string           `json:"permission_level"`
	List         *ClickUpRef      `json:"list"`
	Project      *ClickUpRef      `json:"project"`
	Folder       *ClickUpRef      `json:"folder"`
	Space        *ClickUpSpaceRef `json:"space"`
}

type ClickUpStatus struct {
	ID         string `json:"id"`
	Status     string `json:"status"`
	Color      string `json:"color"`
	OrderIndex int    `json:"orderindex"`
	Type       string `json:"type"`
}

type ClickUpUser struct {
	ID             int     `json:"id"`
	Username       string  `json:"username"`
	Color          string  `json:"color"`
	Email          string  `json:"email"`
	ProfilePicture *string `json:"profilePicture"`
	Initials       string  `json:"initials,omitempty"`
}

type ClickUpRef struct {
	ID     string `json:"id"`
	Name   string `json:"name"`
	Access bool   `json:"access"`
	Hidden bool   `json:"hidden,omitempty"`
}

type ClickUpSpaceRef struct {
	ID string `json:"id"`
}

type CreateClickUpTaskRequest struct {
	Name        string `json:"name" example:"buat tugas"`
	Description string `json:"description" example:"coba post api buat tugas"`
}

type UpdateClickUpTaskRequest struct {
	Name        string `json:"name,omitempty" example:"update nama tugas"`
	Description string `json:"description,omitempty" example:"update deskripsi tugas"`
	Status      string `json:"status,omitempty" example:"to do"`
	DueDate     int64  `json:"due_date,omitempty" example:"1772583367492"`
}

type ClickUpCommentRequest struct {
	Comment string `json:"comment" example:"This is a comment"`
}

type ClickUpAssignRequest struct {
	UserID int `json:"user_id" example:"12345"`
}

type ClickUpRepository interface {
	CreateTask(listID string, task CreateClickUpTaskRequest) (*ClickUpTask, error)
	UpdateTask(taskID string, task UpdateClickUpTaskRequest) error
	GetTaskDetails(taskID string) (*ClickUpTask, error)
	AddComment(taskID string, comment string) error
	AssignTask(taskID string, userID int) error
}

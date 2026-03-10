package logger

import (
	"log"
	"os"
)

type Logger struct {
	infoLog  *log.Logger
	errorLog *log.Logger
}

func NewLogger() *Logger {
	return &Logger{
		infoLog:  log.New(os.Stdout, "INFO: ", log.Ldate|log.Ltime|log.Lshortfile),
		errorLog: log.New(os.Stderr, "ERROR: ", log.Ldate|log.Ltime|log.Lshortfile),
	}
}

func (l *Logger) Info(msg string, args ...interface{}) {
	l.infoLog.Printf(msg, args...)
}

func (l *Logger) Error(msg string, args ...interface{}) {
	l.errorLog.Printf(msg, args...)
}

package logger

import (
	"io"
	"os"
	"strings"

	"github.com/sirupsen/logrus"
)

var (
	Info  = logrus.Info
	Warn  = logrus.Warn
	Error = logrus.Error
	Debug = logrus.Debug
	Fatal = logrus.Fatal
	Infof = logrus.Infof
	Warnf = logrus.Warnf
	Errorf = logrus.Errorf
	Debugf = logrus.Debugf
	Fatalf = logrus.Fatalf
)

// Config represents logger configuration
type Config struct {
	Level  string
	Format string
	File   string
}

// Init initializes the logger with the given configuration
func Init(cfg Config) {
	// Set log level
	level, err := logrus.ParseLevel(cfg.Level)
	if err != nil {
		level = logrus.InfoLevel
	}
	logrus.SetLevel(level)

	// Set log format
	if strings.ToLower(cfg.Format) == "json" {
		logrus.SetFormatter(&logrus.JSONFormatter{
			TimestampFormat: "2006-01-02 15:04:05",
		})
	} else {
		logrus.SetFormatter(&logrus.TextFormatter{
			FullTimestamp:   true,
			TimestampFormat:   "2006-01-02 15:04:05",
		})
	}

	// Set output
	var output io.Writer = os.Stdout
	if cfg.File != "" {
		file, err := os.OpenFile(cfg.File, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
		if err != nil {
			logrus.Warnf("Failed to open log file %s: %v", cfg.File, err)
		} else {
			output = file
		}
	}
	logrus.SetOutput(output)
}
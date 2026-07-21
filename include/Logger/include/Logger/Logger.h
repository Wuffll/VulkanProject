#ifndef LOGGER_H
#define LOGGER_H

#if __cplusplus < 201703L

#include <string>

#endif

#if __cplusplus >= 201703L

#include <string_view>

#endif

#if __cplusplus >= 202002L

#include <source_location>

#endif

#if __cplusplus < 202002L

#define LOGGER_LOG(InLevel, InMessage) Logger::Log(InLevel, InMessage, __func__, __FILE__, __LINE__)

#endif

enum class LogLevel
{
    Info,
    Warning,
    Error,
    Fatal
};

class Logger
{

public:

    #if __cplusplus >= 202002L
    static void Log(LogLevel InLevel,
                    std::string_view InMessage,
                    std::source_location const Source = std::source_location::current());
    #elif __cplusplus >= 201703L
    static void Log(LogLevel InLevel, std::string_view InMessage, const char* InFuncName, const char* InFile, int InLine);
    #else
    static void Log(LogLevel InLevel, const std::string& InMessage, const char* InFuncName, const char* InFile, int InLine);
    #endif

};


#endif // LOGGER_H

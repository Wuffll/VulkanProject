//
// Created by ae on 19. 07. 2026..
//

#include "Logger/Logger.h"

#include <iostream>
#include <format>
#include <string_view>

const std::string S_FILE_LOG_START_LEVEL = "src";

static const char* LogLevelToCString(LogLevel InLevel)
{
    switch (InLevel)
    {
        case LogLevel::Info:            return "Info";
        case LogLevel::Warning:         return "Warning";
        case LogLevel::Error:           return "Error";
        case LogLevel::Fatal:           return "FATAL";
        default:                        return "Invalid LogLevel";

    }
}

#if __cplusplus >= 202002L
void Logger::Log(LogLevel InLevel,
                 std::string_view InMessage,
                 std::source_location const Source)
{
    std::string_view funcSubstr{ Source.function_name() };
    size_t funcIndex = funcSubstr.rfind(' ');
    funcSubstr = funcSubstr.substr(funcIndex + 1);

    std::string_view fileSubstr{ Source.file_name() };
    size_t fileIndex = fileSubstr.rfind(S_FILE_LOG_START_LEVEL);
    fileSubstr = fileSubstr.substr(fileIndex);

    std::cout <<
    std::format("[{0}] {1}({2}) => {3} | {4}",
                LogLevelToCString(InLevel),
                fileSubstr,
                Source.line(),
                funcSubstr,
                InMessage) <<
                std::endl;
}
#elif __cplusplus >= 201703L
void Logger::Log(LogLevel InLevel,
                 std::string_view InMessage,
                 const char* InFuncName,
                 const char* InFile,
                 int InLine)
{
    std::string_view fileSubstr{ Source.file_name() };
    size_t fileIndex = fileSubstr.rfind(S_FILE_LOG_START_LEVEL);
    fileSubstr = fileSubstr.substr(fileIndex);

    std::cout << "[" << LogLevelToCString(InLevel) << "] "
    << fileSubstr << "(" << InLine << ")"
    << " => " << InFuncName << "()"
    << " | " << InMessage
    << std::endl;;
}
#else
void Logger::Log(LogLevel InLevel,
                 const std::string& InMessage,
                 const char* InFuncName,
                 const char* InFile,
                 int InLine)
{
    std::string fileSubstr{ Source.file_name() };
    size_t fileIndex = fileSubstr.rfind(S_FILE_LOG_START_LEVEL);
    fileSubstr = fileSubstr.substr(fileIndex);

    std::cout << "[" << LogLevelToCString(InLevel) << "] "
    << fileSubstr << "(" << InLine << ")"
    << " => " << InFuncName << "()"
    << " | " << InMessage
    << std::endl;;
}
#endif

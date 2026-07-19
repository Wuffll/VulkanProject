//
// Created by ae on 19. 07. 2026..
//

#include "Logger/Logger.h"

#include <iostream>
#include <format>
#include <string_view>

static const char* S_SRC_DIRECTORY_NAME = "src";

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

void Logger::Log(LogLevel InLevel,
    std::string_view InMessage,
    std::source_location const Source)
{
    std::string_view sourceSubstr{ Source.file_name() };
    size_t srcIndex = sourceSubstr.rfind(S_SRC_DIRECTORY_NAME);
    sourceSubstr = sourceSubstr.substr(srcIndex);

    std::string_view funcSubstr{ Source.function_name() };
    size_t funcIndex = funcSubstr.rfind(' ');
    funcSubstr = funcSubstr.substr(funcIndex + 1);

    std::cout <<
        std::format("[{0}] {1}({2}) => {3} | {4}",
            LogLevelToCString(InLevel),
            sourceSubstr,
            Source.line(),
            funcSubstr,
            InMessage) <<
        std::endl;
}

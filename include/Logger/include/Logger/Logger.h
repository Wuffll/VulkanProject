//
// Created by ae on 19. 07. 2026.
//

#ifndef VULKANPROJECT_LOGGER_H
#define VULKANPROJECT_LOGGER_H

#include <string_view>
#include <source_location>

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

    static void Log(LogLevel InLevel, std::string_view InMessage,
        std::source_location Source = std::source_location::current());

};


#endif //VULKANPROJECT_LOGGER_H

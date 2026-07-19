//
// Created by ae on 19. 07. 2026.
//

#include "DummyLibrary/DummyLibrary.h"

#include <string>

namespace VulkanApp
{
    DummyLibrary::DummyLibrary()
    {
        _dummyInt = 5;
    }

    void DummyLibrary::DummyFunction()
    {
        int x = 5;
        x += x;

        std::string message = "What am I doing right now?";
    }
}
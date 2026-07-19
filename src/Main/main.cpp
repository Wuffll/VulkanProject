
#include <format>
#include <iostream>

#include "DummyLibrary/DummyLibrary.h"
#include "Logger/Logger.h"
#include "assimp/vector3.h"

std::string Vec3ToString(const aiVector3f& InVector)
{
    return std::format("({0}, {1}, {2})", InVector.x, InVector.y, InVector.z);
}

int main()
{
    VulkanApp::DummyLibrary::DummyFunction();


    const aiVector3f vector{0.0f};

    std::cout << Vec3ToString(vector) << std::endl;
    Logger::Log(LogLevel::Info, "Testing");

    return 0;
}
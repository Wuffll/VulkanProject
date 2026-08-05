#include <iostream>
#include <stdexcept>
#include <cstdlib>

#include "AppVulkan/App.h"

int main()
{
    try
    {
        vp::HelloTriangleApplication app;
        app.Run();
    }
    catch (const std::exception& e)
    {
        std::cerr << e.what() << std::endl;
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
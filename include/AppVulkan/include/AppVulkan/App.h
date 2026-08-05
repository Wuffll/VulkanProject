#ifndef APPVULKAN_APP_H
#define APPVULKAN_APP_H

#if defined(__INTELLISENSE__) || !defined(USE_CPP20_MODULES)
#include <vulkan/vulkan_raii.hpp>
#else
import vulkan_hpp;
#endif
#include <GLFW/glfw3.h>


namespace vp {

    class HelloTriangleApplication {
    public:

        void Run();

    private:

        void InitVulkan();

        void MainLoop();

        void Cleanup();

    };

} // namespace vp
#endif // APPVULKAN_APP_H

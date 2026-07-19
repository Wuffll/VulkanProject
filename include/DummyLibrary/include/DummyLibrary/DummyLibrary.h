#ifndef _VULKANAPP_DUMMYLIBRARY_HPP_
#define _VULKANAPP_DUMMYLIBRARY_HPP_

namespace VulkanApp
{
    class DummyLibrary
    {
    protected:

        int _dummyInt;

    public:

        DummyLibrary();

        static void DummyFunction();

    };
}

#endif
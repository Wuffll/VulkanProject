# VulkanProject - Personal Vulkan Playground

## Introduction

This repository contains project files for my personal learning progress with Vulkan (and reintroduction to CMake). 


Currently, the project is in a very early stage, so there are no official guidelines and/or build instructions for
the project. As the project grows, there will be separate sections such as *"Build instructions"*, *"Code examples"*
and more.

## Build instructions

Since the project is in its early stage, I haven't tested building this project on different platforms. 
The following are instructions for building the project.

Requirements:
  - CMake 4.4.0 or higher (Assimp library requires 4.4.0 or higher)
  - Vulkan
  - C/C++ compiler setup (clang and gcc worked for me on Arch Linux)

To build this project, it is recommended to create a separate build directory and create a build there via CMake.
You can do that with the following commands:

```bash
# in project root directory
mkdir build
cd build
cmake ..
cmake --build .
```

CMake will do everything else for you. You have to make sure you have a compiler for C/C++ installed.

If you do encounter an error that you think is due to the misconfiguration of CMake,
please let me know through [Github Issues](https://github.com/Wuffll/VulkanProject/issues).
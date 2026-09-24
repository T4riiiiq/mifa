#include <iostream>

int main()
{
    std::cout << "Mifa Operational Package\n";
    std::cout << "Build ID: {{BUILD_ID}}\n";
    std::cout << "Architecture: {{ARCH}}\n";
    std::cout << "Build type: {{BUILD_TYPE}}\n";
    std::cout << "Payload type: {{PAYLOAD_TYPE}}\n";
    std::cout << "Payload transform: {{PAYLOAD_TRANSFORM}}\n";
    std::cout << "Payload source: {{PAYLOAD_SOURCE_NAME}}\n";
    std::cout << "Payload size: {{PAYLOAD_SOURCE_SIZE}}\n";
    std::cout << "Payload SHA256: {{PAYLOAD_SOURCE_SHA256}}\n";
    std::cout << "Staged SHA256: {{PAYLOAD_STAGED_SHA256}}\n";

    return 0;
}

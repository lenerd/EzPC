set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
include(cmake/source_of_randomness.cmake)

find_package(OpenSSL REQUIRED)
find_package(GMP REQUIRED)

add_library(SCI-utils INTERFACE)

target_include_directories(SCI-utils
    INTERFACE ${OPENSSL_INCLUDE_DIR} ${GMP_INCLUDE_DIR}
)

target_link_libraries(SCI-utils
    INTERFACE ${OPENSSL_LIBRARIES} ${GMP_LIBRARIES}
)

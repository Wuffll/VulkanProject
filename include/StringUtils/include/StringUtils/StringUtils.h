#if __cplusplus < 201703L

#include <string>

typedef const std::string& StringViewArgAlias;
typedef std::string StringViewReturnAlias;

#else

#include <string_view>

using StringViewArgAlias = std::string_view;
using StringViewReturnAlias = std::string_view;

#endif

#include <vector>


class StringUtils
{

public:

    static std::vector<StringViewReturnAlias> Tokenize(StringViewArgAlias InStringView, StringViewArgAlias InDelim);
};

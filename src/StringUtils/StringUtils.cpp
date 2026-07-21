#include "StringUtils/StringUtils.h"

#include <iostream>
#include <string>

std::vector<StringViewReturnAlias> StringUtils::Tokenize(StringViewArgAlias InString, StringViewArgAlias InDelim)
{
    if (InString.empty() || InDelim.empty())
    {
        return std::vector<StringViewReturnAlias>{};
    }

    std::vector<StringViewReturnAlias> result{};

    std::vector<int> foundDelimIndices{};
    foundDelimIndices.reserve(8);

    size_t start = 0;
    while (true) {
        start = InString.find_first_not_of(InDelim, start);
        if (start == std::string::npos)
        {
            break;
        }

        auto end = InString.find_first_of(InDelim, start);

        foundDelimIndices.push_back(end);

        if (end == std::string::npos)
        {
            break;
        }
        start = end == std::string::npos ? end : end + 1;


    }

    const int delimCounter = foundDelimIndices.size();
    if(delimCounter == 0)
    {
        return result;
    }

    result.reserve(delimCounter);

    for(int i = 0; i < delimCounter; i++)
    {
        const int startIndex = i == 0 ? 0 : foundDelimIndices[i - 1] + 1;
        const int endIndex = foundDelimIndices[i];

        StringViewReturnAlias currentSubstring{
            InString.substr(startIndex, endIndex - startIndex)};

        result.emplace_back(currentSubstring);
    }

    return result;
}

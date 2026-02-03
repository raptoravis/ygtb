---
name: style-generator
description: Analyze reference articles and generate detailed writing style descriptions. Use when you need to extract and describe the writing style from one or more reference articles. This skill guides the AI assistant to analyze writing characteristics like tone, vocabulary, sentence structure, and rhetorical devices, then output a comprehensive style description for later use in rewriting other content.
---

# Style Generator

Generate detailed style descriptions from reference articles.

## When to Use

Use this skill when you have one or more reference articles and need to:
- Extract the writing style characteristics
- Create a style description for later use
- Analyze tone, vocabulary, structure, and rhetorical patterns

## Workflow

1. **Receive Reference Articles**: The user provides one or more reference articles
2. **Analyze Style**: Systematically analyze the writing characteristics
3. **Generate Description**: Output a detailed, structured style description

## Analysis Framework

When analyzing reference articles, examine these dimensions:

### 1. Writing Style Category
- Formal vs Casual
- Academic vs Literary vs Business
- Technical vs General audience
- Narrative vs Expository vs Persuasive

### 2. Language Characteristics
- Vocabulary preferences (simple vs complex, abstract vs concrete)
- Sentence structure (short vs long, varied vs uniform)
- Rhetorical devices (metaphors, analogies, repetition)
- Transition words and connectors

### 3. Emotional Tone
- Serious vs Lighthearted
- Enthusiastic vs Objective
- Authoritative vs Friendly
- Urgent vs Relaxed

### 4. Article Structure
- Opening patterns (hook, context, thesis)
- Body organization (chronological, logical, thematic)
- Closing techniques (summary, call-to-action, reflection)
- Paragraph length and flow

### 5. Special Expression Habits
- Unique phrases or expressions
- Parenthetical remarks
- Questions or rhetorical questions
- Direct address to reader

## Output Format

Generate a style description in this structure:

```
【风格名称】：[用户指定的名称]

【写作风格】：[正式/随意/学术/文学/商务等]

【语言特点】：
- 用词习惯：[描述]
- 句式结构：[描述]
- 修辞手法：[描述]

【情感基调】：[严肃/轻松/热情/客观等]

【文章结构】：
- 开头：[描述]
- 正文：[描述]
- 结尾：[描述]

【特殊表达习惯】：[描述]

【整体风格描述】：
[一段连贯的总结性描述，让AI能够理解并模仿这种风格]
```

## Usage Example

User: "请分析以下两篇文章的风格并生成风格描述"

[用户提供参考文章]

Claude: 
1. 阅读参考文章
2. 按照分析框架进行系统性分析
3. 输出结构化的风格描述
4. 确认用户是否需要调整

## Important Notes

- Be specific and concrete in descriptions
- Include examples from the reference text when helpful
- The description should be detailed enough for AI to replicate the style
- Ask for clarification if reference articles are unclear or inconsistent in style
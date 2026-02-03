---
name: style-generator
description: Writing style analysis and management tool. Generate prompts for analyzing reference articles and creating detailed writing style descriptions. Use when you need to extract and describe writing style from one or more reference articles.
---

# Style Generator

Manage reference articles and generate prompts for style analysis.

## When to Use

Use this skill when you have one or more reference articles and need to:

- Extract writing style characteristics
- Create a style description for later use
- Analyze tone, vocabulary, structure, and rhetorical patterns

## Workflow

1. **Get the style by the style name**: Use the script to get the style as the provided style name might be fuzzy
2. **Generate Prompt**: Use the script to generate a complete LLM prompt
3. **Use the Prompt**:
4. **Save Result**: Save the rewritten article for the ref

## Analysis Framework

When analyzing reference articles, the LLM should examine these dimensions:

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

## Command Line Usage

### Generate Style Analysis Prompt

```bash
uv run python skills/style-generator/scripts/generate_style.py \
    --articles article1.txt,article2.txt \
    --style-name "我的风格" \
    --generate-prompt
```

The script will output a complete prompt that you can send to an LLM:

```text
你是一个专业的写作风格分析专家，能够准确捕捉文章的写作风格、语气、用词习惯和结构特点，并用简洁准确的语言描述这些风格特点。

分析以下参考文章的风格特点，生成一个详细的风格描述。

风格名称: 我的风格

参考文章:
参考文章1:
[文章1内容...]

参考文章2:
[文章2内容...]

请分析参考文章的以下方面，并生成一个清晰、详细的风格描述：
1. 写作风格（正式/随意/学术/文学等）
2. 语言特点（用词习惯、句式结构、修辞手法等）
3. 情感基调（严肃/轻松/热情/客观等）
4. 文章结构（开头/正文/结尾的组织方式）
5. 特殊的表达习惯或写作手法

请将以上分析整合成一个连贯、详细的风格描述，这个描述将用于指导AI以相同的风格重写其他文章。
描述应该具体、准确，足以让AI理解和模仿这种写作风格。
```

### Save Style Description to File

After obtaining the style description from LLM:

```bash
# First, save the LLM result to a file
echo "风格描述内容..." > style_description.txt

# Then save to style database
uv run python skills/style-generator/scripts/generate_style.py \
    --articles article1.txt,article2.txt \
    --style-name "我的风格" \
    --style-description-file style_description.txt \
    --save
```

This will add the style to `data/articles.json`, making it available for use by `article-rewriter`.

### Use in uv run python

```uv run python
from utils import save_styles, load_styles

# Save style programmatically
styles = load_styles()
new_style = {
    "name": "我的风格",
    "description": "风格描述内容...",
    "additional_instructions": "",
    "articles": [
        {
            "content": "参考文章1...",
            "time": "2026-02-03 12:00:00"
        }
    ]
}
styles.append(new_style)
save_styles(styles)
```

## Important Notes

- Be specific and concrete in descriptions
- Include examples from reference text when helpful
- The description should be detailed enough for AI to replicate style
- Ask for clarification if reference articles are unclear or inconsistent in style

## Skill Execution for AI Assistant

When this skill is invoked, the AI assistant should:

1. Read the reference articles
2. Generate a complete style analysis prompt
3. Call an external LLM with the prompt
4. Return the style description
5. Optionally save to style database if requested

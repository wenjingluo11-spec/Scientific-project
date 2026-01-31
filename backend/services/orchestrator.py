from typing import Optional, List, Dict
from utils.anthropic_client import AnthropicClient
from models.paper import Paper, AgentConversation
from models.topic import Topic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import json
from config import settings


class AgentOrchestrator:
    """Multi-agent orchestrator for paper generation"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = AnthropicClient()
        self.agent_roles = [
            "research_director",
            "literature_researcher",
            "methodology_expert",
            "data_analyst",
            "paper_writer",
            "peer_reviewer",
        ]

    async def generate_paper(
        self,
        topic_ids: List[int],
        paper_id: Optional[int] = None,
        progress_callback=None,
        use_deep_research: bool = False
    ) -> Paper:
        """
        Orchestrate multi-agent paper generation workflow
        
        Args:
            topic_ids: The research topic IDs (list)
            paper_id: Optional existing paper ID to use
            progress_callback: Optional callback for progress updates
            use_deep_research: Whether to use Gemini Deep Research for writing
        """

        # Get topics
        result = await self.db.execute(select(Topic).where(Topic.id.in_(topic_ids)))
        topics = result.scalars().all()
        if not topics:
            raise ValueError(f"Topics {topic_ids} not found")

        # Get or Create paper record
        if paper_id:
            result = await self.db.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if not paper:
                raise ValueError(f"Paper {paper_id} not found")
            paper.status = "processing"
        else:
            paper = Paper(
                topic_id=topic_ids[0],
                topic_ids=json.dumps(topic_ids),
                title=f"Research on {', '.join([t.title for t in topics])}"[:500],
                status="processing",
            )
            self.db.add(paper)
        
        await self.db.commit()
        await self.db.refresh(paper)

        # Context accumulation
        context = {
            "topics": [t.to_dict() for t in topics],
            "literature_review": "",
            "methodology": "",
            "data_analysis": "",
            "draft": "",
            "review": "",
        }

        try:
            # Deep Research Direct Mode: Skip multi-agent workflow
            if use_deep_research:
                print("[Orchestrator] Deep Research Direct Mode activated - skipping multi-agent workflow", flush=True)
                return await self._generate_with_deep_research(
                    paper=paper,
                    topics=topics,
                    progress_callback=progress_callback
                )

            # Standard Multi-Agent Workflow
            # Step 1: Research Director Analysis
            await self._update_progress(progress_callback, "research_director", "working", 10, "研究主管正在规划研究大纲与任务分配...", paper_id=paper.id)
            
            # Combine topic info for the director
            combined_topics_info = "\n\n".join([
                f"选题 {i+1}:\n标题: {t.title}\n描述: {t.description}\n领域: {t.field}\n关键词: {', '.join(json.loads(t.keywords) if t.keywords else [])}"
                for i, t in enumerate(topics)
            ])

            director_analysis = await self._run_agent(
                "research_director",
                f"分析以下多个研究选题的关联性，并制定一个综合研究计划：\n\n"
                f"{combined_topics_info}",
                paper.id,
                step_name="Research Plan"
            )
            await self._update_progress(progress_callback, "research_director", "completed", 15, "研究计划已制定完成", paper_id=paper.id)

            # Step 2: Literature Research
            await self._update_progress(progress_callback, "literature_researcher", "working", 20, "文献调研员正在检索相关学术资源并进行总结分析...", paper_id=paper.id)
            literature_review = await self._run_agent(
                "literature_researcher",
                f"基于以下研究计划，进行文献调研：\n\n{director_analysis}\n\n"
                f"请搜索相关文献，总结研究现状、关键发现和研究空白。",
                paper.id,
                step_name="Literature Review"
            )
            context["literature_review"] = literature_review
            await self._update_progress(progress_callback, "literature_researcher", "completed", 35, "文献调研已完成", paper_id=paper.id)

            # Step 3: Methodology Design
            await self._update_progress(progress_callback, "methodology_expert", "working", 40, "方法论专家正在构建研究框架与实验逻辑...", paper_id=paper.id)
            methodology = await self._run_agent(
                "methodology_expert",
                f"基于文献调研结果，设计研究方法：\n\n{literature_review}\n\n"
                f"请提供详细的研究方法、实验设计和数据采集方案。",
                paper.id,
                step_name="Methodology Design"
            )
            context["methodology"] = methodology
            await self._update_progress(progress_callback, "methodology_expert", "completed", 50, "研究方法设计完成", paper_id=paper.id)

            # Step 4: Data Analysis Plan
            await self._update_progress(progress_callback, "data_analyst", "working", 55, "数据分析师正在制定统计策略与结果验证方案...", paper_id=paper.id)
            data_analysis = await self._run_agent(
                "data_analyst",
                f"基于研究方法，提供数据分析方案：\n\n{methodology}\n\n"
                f"请建议统计方法、数据可视化方案和结果验证方法。",
                paper.id,
                step_name="Data Analysis Plan"
            )
            context["data_analysis"] = data_analysis
            await self._update_progress(progress_callback, "data_analyst", "completed", 65, "数据分析方案已锁定", paper_id=paper.id)

            # Step 5: Paper Writing
            writer_status_msg = "学术撰写专家正在整合所有研究成果，撰写论文初稿..."
            if use_deep_research:
                writer_status_msg += " (已启用 Gemini Deep Research 深度模式)"
            
            await self._update_progress(progress_callback, "paper_writer", "working", 70, writer_status_msg, paper_id=paper.id)
            
            draft_content = await self._run_agent(
                "paper_writer",
                f"基于以上所有信息，撰写完整的学术论文：\n\n"
                f"## 研究计划\n{director_analysis}\n\n"
                f"## 文献综述\n{literature_review}\n\n"
                f"## 研究方法\n{methodology}\n\n"
                f"## 数据分析\n{data_analysis}\n\n"
                f"请撰写包含标题、摘要、引言、方法、结果、讨论、结论和参考文献的完整论文。使用Markdown格式。",
                paper.id,
                step_name="First Draft",
                use_deep_research=use_deep_research # Pass flag specifically for this step
            )
            context["draft"] = draft_content
            await self._update_progress(progress_callback, "paper_writer", "completed", 85, "论文初稿撰写完成", paper_id=paper.id)

            # Step 6: Peer Review & Revision Loop
            # Step 6: Peer Review & Revision Loop
            paper = await self._run_peer_review_loop(self.db, paper, draft_content, progress_callback)

            return paper

        except Exception as e:
            print(f"Error in paper generation: {e}")
            paper.status = "error"
            await self.db.commit()
            raise

    async def _run_peer_review_loop(
        self,
        db_session: AsyncSession,
        paper: Paper,
        draft_content: str,
        progress_callback=None
    ) -> Paper:
        """Run the Peer Review and Revision loop"""
        
        max_iterations = 5  # 最大修改轮数
        current_iteration = 0
        quality_score = 0.0
        detailed_scores = {}
        context = {} # Local context for this loop

        # Step 6: Peer Review & Revision Loop
        await self._update_progress(progress_callback, "peer_reviewer", "working", 90, "同行评审专家正在进行严苛的匿名评审...", paper_id=paper.id)
        
        review_result = await self._run_agent(
            "peer_reviewer",
            f"请严格评审以下论文：\n\n{draft_content}\n\n"
            f"请按照 ICLR/NeurIPS 顶会标准评审，提供具体维度的评分和改进建议。",
            paper.id,
            iteration=current_iteration + 1,
            step_name="Initial Peer Review",
            db_session=db_session
        )
        context["review"] = review_result

        # Extract quality score and detailed scores immediately
        quality_score, detailed_scores = self._extract_detailed_scores(review_result)

        # Update paper progress with initial scores
        await self._update_progress(
            progress_callback, 
            "peer_reviewer", 
            "working", 
            92, 
            f"初步评审已完成，综合评分: {quality_score}", 
            paper_id=paper.id,
            scores=detailed_scores
        )

        # Revision Loop - Threshold is now ALL dimensions must be Perfect (10.0)
        def criteria_met(scores):
            return (scores.get('novelty', 0) >= 10.0 and 
                    scores.get('quality', 0) >= 10.0 and 
                    scores.get('clarity', 0) >= 10.0)

        while not criteria_met(detailed_scores) and current_iteration < max_iterations:
            current_iteration += 1
            
            # Dynamic Progress Update
            progress_percent = 92 + (current_iteration / max_iterations) * 5
            await self._update_progress(
                progress_callback,
                "paper_revisor",
                "working",
                int(progress_percent),
                f"正在进行第 {current_iteration} 轮迭代修正(目标:满分)，当前各维评分 (N:{detailed_scores.get('novelty')}, Q:{detailed_scores.get('quality')}, C:{detailed_scores.get('clarity')})...",
                paper_id=paper.id,
                scores=detailed_scores
            )

            # 1. Revision Agent
            revision_task = (
                f"这是当前的论文草稿：\n\n{draft_content}\n\n"
                f"这是同行评审的意见及其维度的评分：\n\n{review_result}\n\n"
                f"请根据以上意见，对论文进行深度重构和完善。我们的目标极其严格：必须确保创新性(Novelty)、质量(Quality)和清晰度(Clarity)这三个维度的评分全部达到满分 (10.0)。\n"
                f"目前短板维度请重点加强。"
            )

            draft_content = await self._run_agent(
                "paper_revisor",
                revision_task,
                paper.id,
                iteration=current_iteration,
                step_name=f"Revision Round {current_iteration}",
                db_session=db_session
            )

            # 2. Re-Review
            await self._update_progress(
                progress_callback,
                "peer_reviewer",
                "reviewing_revision",
                int(progress_percent + 1),
                message=f"正在评估第 {current_iteration} 轮修正效果...",
                paper_id=paper.id
            )

            review_result = await self._run_agent(
                "peer_reviewer",
                f"这是根据您之前的意见修改后的论文版本：\n\n{draft_content}\n\n"
                f"请重新进行严格评审和评分。之前的意见是：{review_result}",
                paper.id,
                iteration=current_iteration + 1,
                step_name=f"Peer Review Round {current_iteration}",
                db_session=db_session
            )

            # Update Score and detailed breakdown
            quality_score, detailed_scores = self._extract_detailed_scores(review_result)
            context["review"] = review_result

        # Log final status
        await self._update_progress(
            progress_callback, 
            "peer_reviewer", 
            "completed", 
            98, 
            "评审与修正工作全部结束", 
            paper_id=paper.id,
            scores=detailed_scores
        )

        # Update paper with final content
        paper.content = draft_content
        paper.abstract = self._extract_abstract(draft_content)
        paper.quality_score = quality_score
        paper.detailed_scores = json.dumps(detailed_scores)
        paper.status = "completed"

        await db_session.commit()
        await db_session.refresh(paper)

        # CRITICAL: Send progress update AFTER saving the paper content
        await self._update_progress(progress_callback, "completed", "completed", 100, "论文已发表至您的仓库", paper_id=paper.id)

        return paper

    async def _run_agent(
        self,
        role: str,
        task: str,
        paper_id: int,
        iteration: int = 1,
        step_name: str = None,
        use_deep_research: bool = False,
        db_session: Optional[AsyncSession] = None
    ) -> str:
        """Run a single agent and save conversation"""

        if use_deep_research and role == "paper_writer":
            from utils.gemini_client import GeminiDeepResearchClient
            # Explicitly pass the Google API Key from settings
            deep_client = GeminiDeepResearchClient(api_key=settings.GOOGLE_API_KEY)
            
            print(f"[Orchestrator] Using Gemini Deep Research for {role}...", flush=True)
            
            # Run research task - NO try/except fallback needed as per requirements
            # If this fails, it should propagate the exception up
            response_text = await deep_client.run_research_task(task)
            
            # Add signature
            response = response_text + f"\n\n-- Generated by Gemini Deep Research --"
        else:
            response = await self.client.create_message(
                role=role,
                context="",
                task=task,
            )


        # Extract signature and clean content
        model_signature, cleaned_content = self._extract_signature_and_clean(response)

        # Use provided session or default to self.db
        session = db_session if db_session else self.db

        # Save conversation with traceability info
        conversation = AgentConversation(
            paper_id=paper_id,
            agent_role=role,
            message=cleaned_content, # Save cleaned content
            iteration=iteration,
            step_name=step_name or role,
            input_context=task, # Save the input task as context
            model_signature=model_signature
        )
        session.add(conversation)
        await session.commit()

        return cleaned_content

    def _extract_signature_and_clean(self, content: str):
        """Extract model signature and clean reasoning/meta-content"""
        import re

        # 1. Remove <think>...</think> blocks (DeepSeek style)
        cleaned_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

        # 2. Extract signature (last line)
        lines = cleaned_content.split('\n')
        signature = None
        
        if lines:
            last_line = lines[-1].strip()
            if last_line.startswith("-- Generated by") and last_line.endswith("--"):
                signature = last_line
                lines = lines[:-1]
                cleaned_content = '\n'.join(lines).strip()

        # 3. Aggressive Preamble Removal
        # Strategy: Find the first occurrence of a Markdown Header (#, ##, ###) or "Abstract"
        # and discard everything before it. This handles cases like "Sure! Here is the paper:\n\n# The Paper Title..."
        
        match = re.search(r'(^|\n)(#+\s|Abstract|摘要)', cleaned_content, re.IGNORECASE)
        if match:
            # If the match starts with a newline, we want to include it or trim nicely, 
            # effectively we want the content starting from the header line
            # match.start() gives index of newline if group 1 matched newline
            # simpler: split at the match, keep only the second part (and re-add the separator if needed)
            
            # actually, simpler approach:
            # content[start_index:].lstrip() might leave the newline.
            # let's be precise.
            
            # If group 1 matched newline, the header starts at match.start() + 1
            if match.group(0).startswith('\n'):
                cleaned_content = cleaned_content[match.start()+1:]
            else:
                cleaned_content = cleaned_content[match.start():]
        else:
            # Fallback: Remove specific conversational markers
            conversational_prefixes = [
                "Certainly!", "Sure,", "Here is", "Below is", 
                "你好", "好的", "当然", "以下是", "修订后的"
            ]
            for prefix in conversational_prefixes:
                if cleaned_content.strip().startswith(prefix):
                    # Try to find the next double newline which usually starts the content
                    parts = cleaned_content.split('\n\n', 1)
                    if len(parts) > 1:
                        cleaned_content = parts[1]
                    break
        
        cleaned_content = cleaned_content.strip() # Ensure final content is stripped

        # Fallback if signature not found
        if not signature:
            # Use default model from client if available
            signature = f"-- Generated by {self.client.model} (Fallback) --"

        return signature, cleaned_content

    async def _get_topic(self, topic_id: int) -> Optional[Topic]:
        """Get topic by ID"""
        result = await self.db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        return result.scalar_one_or_none()

    async def _update_progress(self, callback, agent: str, status: str, progress: int, message: str = None, paper_id: int = None, scores: dict = None):
        """Update progress via callback"""
        if callback:
            msg = message if message else f"{agent} is {status}"
            payload = {
                "agent": agent,
                "status": status,
                "progress": progress,
                "message": msg,
            }
            if paper_id:
                payload["paperId"] = paper_id
            if scores:
                payload["detailedScores"] = scores
            await callback(payload)

    def _extract_detailed_scores(self, review: str) -> tuple[float, dict]:
        """Extract multi-dimensional scores from review JSON"""
        import re
        import json

        total_score = self._extract_quality_score(review)
        # Default to 0.0 if specific ones can't be parsed
        # This forces the loop to continue if parsing fails (as 0 < 10)
        detailed = {
            "novelty": 0.0, 
            "quality": 0.0, 
            "clarity": 0.0, 
            "total": total_score
        }

        try:
            json_match = re.search(r'\{.*\}', review, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if "scores" in data:
                    s = data["scores"]
                    detailed["novelty"] = float(s.get("novelty", detailed["novelty"]))
                    detailed["quality"] = float(s.get("quality", detailed["quality"]))
                    detailed["clarity"] = float(s.get("clarity", detailed["clarity"]))
                    total_score = float(s.get("total", total_score))
                    detailed["total"] = total_score
                    return total_score, detailed
        except Exception as e:
            print(f"Error extracting detailed scores: {e}")

        return total_score, detailed

    def _extract_quality_score(self, review: str) -> float:
        """Extract quality score from review text (1-10 scale)"""
        import re
        import json

        # 1. Try parsing JSON block
        try:
            json_match = re.search(r'\{.*\}', review, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if "scores" in data and "total" in data["scores"]:
                    return float(data["scores"]["total"])
                if "total" in data:
                    return float(data["total"])
                if "score" in data:
                    return float(data["score"])
        except:
            pass

        # 2. Regex Patterns for 1-10 scale
        patterns = [
            r'"total":\s*(\d+(?:\.\d+)?)',
            r'总分[：:]\s*(\d+(?:\.\d+)?)',
            r'评分[：:]\s*(\d+(?:\.\d+)?)',
            r'Score[：:]\s*(\d+(?:\.\d+)?)',
            r'\[\s*(\d+(?:\.\d+)?)\s*\]'
        ]

        for pattern in patterns:
            match = re.search(pattern, review, re.IGNORECASE)
            if match:
                val = float(match.group(1))
                if 1 <= val <= 10:
                    return val
                if 10 < val <= 100: # Handle accidental 0-100 scale
                    return val / 10.0

        # 3. Last resort - find any number 1-10
        numbers = re.findall(r'(\d+(?:\.\d+)?)', review)
        for n in numbers:
            val = float(n)
            if 3 <= val <= 10: # Likely a score
                return val

        return 7.0 # Default "Borderline Accept"

    def _extract_abstract(self, content: str) -> str:
        """Extract abstract from paper content"""
        try:
            import re
            # Look for Abstract section
            match = re.search(r'#+\s*(?:Abstract|摘要)\s*\n+(.*?)(?=\n#+|\Z)', content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()[:500]

            # Fallback: return first paragraph
            paragraphs = content.split('\n\n')
            for p in paragraphs:
                if len(p.strip()) > 50:
                    return p.strip()[:500]

            return "No abstract available"
        except:
            return "No abstract available"

    async def _generate_with_deep_research(
        self,
        paper: Paper,
        topics: list,
        progress_callback=None
    ) -> Paper:
        """
        Direct paper generation using Gemini Deep Research.
        Skips multi-agent workflow and generates complete paper with specialized prompt.
        """
        from utils.gemini_client import GeminiDeepResearchClient
        
        # Prepare topics info
        topics_info = "\n\n".join([
            f"### 选题 {i+1}\n"
            f"- **标题**: {t.title}\n"
            f"- **描述**: {t.description}\n"
            f"- **领域**: {t.field}\n"
            f"- **关键词**: {', '.join(json.loads(t.keywords) if t.keywords else [])}"
            for i, t in enumerate(topics)
        ])

        # Specialized comprehensive prompt for Deep Research (English)
        deep_research_prompt = f"""You are a world-class academic research expert with deep interdisciplinary expertise. Based on the following research topics, write a high-quality academic paper.

## Research Topics

{topics_info}

## Research Tasks

Please complete the following comprehensive research work:

### 1. Literature Review
- Search for the latest academic literature in this field (primarily from the past 5 years)
- Summarize the current state of research, major schools of thought, and cutting-edge developments
- Identify gaps and limitations in existing research

### 2. Research Design
- Formulate clear research questions and hypotheses
- Design appropriate research methods and technical approaches
- Plan experimental schemes or data analysis strategies

### 3. Paper Writing

Please produce a complete academic paper with the following structure:

#### Title
- Concise, accurate, and compelling

#### Abstract
- 300-500 words summarizing the research

#### Keywords
- 5-8 relevant keywords

#### 1. Introduction
- Research background and significance
- Problem statement
- Research objectives and contributions
- Paper structure

#### 2. Literature Review
- Relevant theoretical foundations
- Current state of research
- Limitations of existing studies
- Innovations of this research

#### 3. Methodology
- Research framework
- Data sources and processing
- Detailed technical methods
- Experimental design

#### 4. Results and Analysis
- Experimental environment and parameter settings
- Results presentation (including tables and figure descriptions)
- Result analysis and discussion
- Comparison with existing methods

#### 5. Discussion
- In-depth discussion of main findings
- Theoretical contributions and practical implications
- Research limitations

#### 6. Conclusion and Future Work
- Main conclusions
- Future research directions

#### References
- Use standard academic citation format (APA, IEEE, or appropriate for the field)
- Prioritize high-quality journals and top-tier conference papers
- Ensure citations are real and verifiable

## Quality Requirements

1. **Novelty**: Present novel perspectives, methods, or findings
2. **Rigor**: Clear logical argumentation and scientifically sound methods
3. **Completeness**: Complete structure with substantial content
4. **Academic Style**: Standard academic language and writing conventions
5. **Target Standard**: Aim for ICLR/NeurIPS/top-tier journal submission quality

Please output the complete paper in Markdown format."""

        try:
            # Step 1: Initialize and start generation
            await self._update_progress(
                progress_callback, 
                "deep_research", 
                "working", 
                10, 
                "🚀 Gemini Deep Research 已启动，正在进行深度研究与论文撰写...",
                paper_id=paper.id
            )

            # Initialize Gemini client
            deep_client = GeminiDeepResearchClient(api_key=settings.GOOGLE_API_KEY)
            
            # Step 2: Run deep research
            await self._update_progress(
                progress_callback,
                "deep_research",
                "researching",
                30,
                "🔍 正在检索文献、分析研究现状...",
                paper_id=paper.id
            )

            # Execute the research task
            # CRITICAL: Close the original DB session before the long wait to prevent connection timeout/InterfaceError
            await self.db.close()
            
            response_text = await deep_client.run_research_task(deep_research_prompt)
            
            await self._update_progress(
                progress_callback,
                "deep_research",
                "writing",
                70,
                "✍️ 论文撰写完成，正在整理格式... (正在重新建立数据库连接)",
                paper_id=paper.id
            )

            # Add signature
            draft_content = response_text + "\n\n-- Generated by Gemini Deep Research (Direct Mode) --"
            
            # Extract and clean content
            model_signature, cleaned_content = self._extract_signature_and_clean(draft_content)

            # -------------------------------------------------------------------------
            # CRITICAL FIX: Use a FRESH database session to save results.
            # The original session (self.db) may have timed out during the long Deep Research call.
            # -------------------------------------------------------------------------
            from models.database import async_session_maker
            from sqlalchemy import select

            async with async_session_maker() as new_db:
                # 1. Re-fetch paper in new session
                result = await new_db.execute(select(Paper).where(Paper.id == paper.id))
                paper_new = result.scalar_one_or_none()
                
                if paper_new:
                    # 2. Save conversation record
                    conversation = AgentConversation(
                        paper_id=paper_new.id,
                        agent_role="deep_research_direct",
                        message=cleaned_content,
                        iteration=1,
                        step_name="Deep Research Direct Generation",
                        input_context=deep_research_prompt[:2000],  # Truncate for storage
                        model_signature=model_signature
                    )
                    new_db.add(conversation)

                    # 3. Save Draft and Interact with Peer Review Loop
                    paper_new.content = cleaned_content
                    paper_new.abstract = self._extract_abstract(cleaned_content)
                    paper_new.status = "reviewing" # Set status to reviewing
                    
                    await new_db.commit()
                    await new_db.refresh(paper_new)

                    # Transition update
                    await self._update_progress(
                        progress_callback,
                        "quality_check",
                        "working",
                        80,
                        "🤖 Deep Research 初稿已生成，即将进入本地专家评审与迭代流程...",
                        paper_id=paper.id
                    )

                    # Handover to Peer Review Loop (using the FRESH session)
                    # The loop will handle further revisions, scoring, and final completion
                    result_paper = await self._run_peer_review_loop(
                        new_db, 
                        paper_new, 
                        cleaned_content, 
                        progress_callback
                    )
                    
                    # Update the local paper object for return (consistency)
                    paper.content = result_paper.content
                    paper.status = result_paper.status
                    paper.quality_score = result_paper.quality_score
                    paper.detailed_scores = result_paper.detailed_scores

            return paper

        except Exception as e:
            print(f"[DeepResearch Direct] Error: {e}", flush=True)
            # Try to save error state using a fresh session as well, as the old one is likely dead
            try:
                from models.database import async_session_maker
                async with async_session_maker() as error_db:
                    result = await error_db.execute(select(Paper).where(Paper.id == paper.id))
                    p = result.scalar_one_or_none()
                    if p:
                        p.status = "error"
                        await error_db.commit()
            except:
                pass # If even that fails, we can't do much
            raise

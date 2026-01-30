from typing import Optional, List, Dict
from utils.anthropic_client import AnthropicClient
from models.paper import Paper, AgentConversation
from models.topic import Topic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import json


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
    ) -> Paper:
        """
        Orchestrate multi-agent paper generation workflow

        Args:
            topic_ids: The research topic IDs (list)
            paper_id: Optional existing paper ID to use
            progress_callback: Optional callback for progress updates

        Returns:
            Generated Paper object
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
            await self._update_progress(progress_callback, "paper_writer", "working", 70, "学术撰写专家正在整合所有研究成果，撰写论文初稿...", paper_id=paper.id)
            draft_content = await self._run_agent(
                "paper_writer",
                f"基于以上所有信息，撰写完整的学术论文：\n\n"
                f"## 研究计划\n{director_analysis}\n\n"
                f"## 文献综述\n{literature_review}\n\n"
                f"## 研究方法\n{methodology}\n\n"
                f"## 数据分析\n{data_analysis}\n\n"
                f"请撰写包含标题、摘要、引言、方法、结果、讨论、结论和参考文献的完整论文。使用Markdown格式。",
                paper.id,
                step_name="First Draft"
            )
            context["draft"] = draft_content
            await self._update_progress(progress_callback, "paper_writer", "completed", 85, "论文初稿撰写完成", paper_id=paper.id)

            # Step 6: Peer Review & Revision Loop
            max_iterations = 5  # 最大修改轮数
            current_iteration = 0
            quality_score = 0.0
            detailed_scores = {}

            # Step 6: Peer Review & Revision Loop
            await self._update_progress(progress_callback, "peer_reviewer", "working", 90, "同行评审专家正在进行严苛的匿名评审...", paper_id=paper.id)
            review_result = await self._run_agent(
                "peer_reviewer",
                f"请严格评审以下论文：\n\n{draft_content}\n\n"
                f"请按照 ICLR/NeurIPS 顶会标准评审，提供具体维度的评分和改进建议。",
                paper.id,
                iteration=current_iteration + 1,
                step_name="Initial Peer Review"
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

            # Revision Loop - Threshold is 9.0
            while quality_score < 9.0 and current_iteration < max_iterations:
                current_iteration += 1
                
                # Dynamic Progress Update
                progress_percent = 92 + (current_iteration / max_iterations) * 5
                await self._update_progress(
                    progress_callback,
                    "paper_revisor",
                    "working",
                    int(progress_percent),
                    f"正在进行第 {current_iteration} 轮迭代修正，当前评分 {quality_score}...",
                    paper_id=paper.id,
                    scores=detailed_scores
                )

                # 1. Revision Agent
                revision_task = (
                    f"这是当前的论文草稿：\n\n{draft_content}\n\n"
                    f"这是同行评审的意见及其维度的评分：\n\n{review_result}\n\n"
                    f"请根据以上意见，重新修改并完善整篇论文，目标是使综合评分达到 9.0（Accept）以上。"
                )

                draft_content = await self._run_agent(
                    "paper_revisor",
                    revision_task,
                    paper.id,
                    iteration=current_iteration,
                    step_name=f"Revision Round {current_iteration}"
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
                    step_name=f"Peer Review Round {current_iteration}"
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

            await self.db.commit()
            await self.db.refresh(paper)

            # CRITICAL: Send progress update AFTER saving the paper content
            await self._update_progress(progress_callback, "completed", "completed", 100, "论文已发表至您的仓库", paper_id=paper.id)

            return paper

        except Exception as e:
            print(f"Error in paper generation: {e}")
            paper.status = "error"
            await self.db.commit()
            raise

    async def _run_agent(
        self,
        role: str,
        task: str,
        paper_id: int,
        iteration: int = 1,
        step_name: str = None,
    ) -> str:
        """Run a single agent and save conversation"""

        response = await self.client.create_message(
            role=role,
            context="",
            task=task,
        )

        # Extract signature and clean content
        model_signature, cleaned_content = self._extract_signature_and_clean(response)

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
        self.db.add(conversation)
        await self.db.commit()

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

        # 3. Final polish: Remove common conversational prefixes if content starts with Markdown headers
        # e.g., "Certainly! Here is the paper: # Title" -> "# Title"
        header_match = re.search(r'(^|\n)(#+ .+)[\s\S]*', cleaned_content)
        if header_match:
            header_start = header_match.start(2)
            # If there's content before the first header, and it's short/conversational, strip it
            prefix = cleaned_content[:header_start].strip()
            if prefix and len(prefix) < 300: # Heuristic: conversational intros are usually short
                cleaned_content = cleaned_content[header_start:].strip()

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
        # Default to base scores derived from total if specific ones can't be parsed
        detailed = {
            "novelty": max(1.0, total_score - 0.5), 
            "quality": total_score, 
            "clarity": min(10.0, total_score + 0.3), 
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

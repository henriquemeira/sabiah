"""Serviço de Métricas e Relatórios."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import Metrica, Conversa, Ticket, Cliente
from src.models.database import get_db
from src.services.notificacao_equipe import ServicoNotificacaoEquipe

logger = logging.getLogger(__name__)


@dataclass
class DadosMetricas:
    """Dados agregados das métricas."""
    total_atendimentos: int
    resolvidos_ia: int
    escalonamentos: int
    tickets_criados: int
    satisfacao_media: Optional[float]
    satisfacao_total: int
    data: datetime


class ServicoMetricas:
    """
    Serviço para gerenciar métricas e relatórios de atendimento.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Inicializa o serviço de métricas.
        
        Args:
            db: Sessão do banco de dados (opcional)
        """
        self._db = db
    
    @property
    def db(self) -> Session:
        """Retorna a sessão do banco de dados."""
        if self._db is None:
            self._db = next(get_db())
        return self._db
    
    def _obter_ou_criar_metrica(self, data: datetime) -> Metrica:
        """
        Obtém ou cria uma métrica para a data especificada.
        
        Args:
            data: Data da métrica
            
        Returns:
            Metrica para a data
        """
        data_inicio = data.replace(hour=0, minute=0, second=0, microsecond=0)
        
        metrica = (
            self.db.query(Metrica)
            .filter(Metrica.data == data_inicio)
            .first()
        )
        
        if not metrica:
            metrica = Metrica(data=data_inicio)
            self.db.add(metrica)
            self.db.commit()
            self.db.refresh(metrica)
        
        return metrica
    
    def registrar_atendimento(
        self,
        resolvido_ia: bool = False,
        escalonado: bool = False,
        ticket_criado: bool = False,
    ) -> Metrica:
        """
        Registra um atendimento nas métricas do dia.
        
        Args:
            resolvido_ia: Se foi resolvido pela IA
            escalonado: Se foi escalonado
            ticket_criado: Se criou um ticket
            
        Returns:
            Metrica atualizada
        """
        hoje = datetime.now()
        metrica = self._obter_ou_criar_metrica(hoje)
        
        metrica.total_atendimentos += 1
        
        if resolvido_ia:
            metrica.resolvidos_ia += 1
        
        if escalonado:
            metrica.escalonamentos += 1
        
        if ticket_criado:
            metrica.tickets_criados += 1
        
        self.db.commit()
        self.db.refresh(metrica)
        
        logger.info(f"📊 Atendimento registrado: total={metrica.total_atendimentos}, "
                   f"resolvidos={metrica.resolvidos_ia}, escalonamentos={metrica.escalonamentos}")
        
        return metrica
    
    def registrar_satisfacao(self, satisfacao: int) -> None:
        """
        Registra uma avaliação de satisfação e recalcula a média.
        
        Args:
            satisfacao: Avaliação de 1-5
        """
        hoje = datetime.now()
        metrica = self._obter_ou_criar_metrica(hoje)
        
        # Calcular nova média
        if metrica.satisfacao_media is None:
            metrica.satisfacao_media = float(satisfacao)
        else:
            # Média móvel simples
            total_avaliacoes = metrica.total_atendimentos
            metrica.satisfacao_media = (
                (metrica.satisfacao_media * (total_avaliacoes - 1) + satisfacao)
                / total_avaliacoes
            )
        
        self.db.commit()
        
        logger.info(f"📊 Satisfação registrada: {satisfacao}, média={metrica.satisfacao_media:.2f}")
    
    def obter_metricas_dia(self, data: Optional[datetime] = None) -> DadosMetricas:
        """
        Obtém as métricas de um dia específico.
        
        Args:
            data: Data (padrão: hoje)
            
        Returns:
            DadosMetricas
        """
        if data is None:
            data = datetime.now()
        
        data_inicio = data.replace(hour=0, minute=0, second=0, microsecond=0)
        data_fim = data_inicio + timedelta(days=1)
        
        # Contagem de conversas
        total_atendimentos = (
            self.db.query(Conversa)
            .filter(
                Conversa.created_at >= data_inicio,
                Conversa.created_at < data_fim,
            )
            .count()
        )
        
        resolvidos_ia = (
            self.db.query(Conversa)
            .filter(
                Conversa.created_at >= data_inicio,
                Conversa.created_at < data_fim,
                Conversa.resolvido == True,  # noqa: E712
            )
            .count()
        )
        
        # Contagem de tickets
        tickets_criados = (
            self.db.query(Ticket)
            .filter(
                Ticket.created_at >= data_inicio,
                Ticket.created_at < data_fim,
            )
            .count()
        )
        
        # Satisfação média
        conversas_com_satisfacao = (
            self.db.query(Conversa)
            .filter(
                Conversa.created_at >= data_inicio,
                Conversa.created_at < data_fim,
                Conversa.satisfacao.isnot(None),
            )
            .all()
        )
        
        if conversas_com_satisfacao:
            satisfacao_media = sum(c.satisfacao for c in conversas_com_satisfacao) / len(conversas_com_satisfacao)
            satisfacao_total = len(conversas_com_satisfacao)
        else:
            satisfacao_media = None
            satisfacao_total = 0
        
        # Escalonamentos (contagem de tickets com prioridade alta)
        escalonamentos = (
            self.db.query(Ticket)
            .filter(
                Ticket.created_at >= data_inicio,
                Ticket.created_at < data_fim,
                Ticket.prioridade == "alta",
            )
            .count()
        )
        
        return DadosMetricas(
            total_atendimentos=total_atendimentos,
            resolvidos_ia=resolvidos_ia,
            escalonamentos=escalonamentos,
            tickets_criados=tickets_criados,
            satisfacao_media=satisfacao_media,
            satisfacao_total=satisfacao_total,
            data=data,
        )
    
    def obter_metricas_periodo(
        self,
        data_inicio: datetime,
        data_fim: Optional[datetime] = None,
    ) -> DadosMetricas:
        """
        Obtém as métricas de um período.
        
        Args:
            data_inicio: Data de início
            data_fim: Data de fim (padrão: agora)
            
        Returns:
            DadosMetricas agregados
        """
        if data_fim is None:
            data_fim = datetime.now()
        
        # Contagem de conversas
        total_atendimentos = (
            self.db.query(Conversa)
            .filter(
                Conversa.created_at >= data_inicio,
                Conversa.created_at < data_fim,
            )
            .count()
        )
        
        resolvidos_ia = (
            self.db.query(Conversa)
            .filter(
                Conversa.created_at >= data_inicio,
                Conversa.created_at < data_fim,
                Conversa.resolvido == True,  # noqa: E712
            )
            .count()
        )
        
        # Contagem de tickets
        tickets_criados = (
            self.db.query(Ticket)
            .filter(
                Ticket.created_at >= data_inicio,
                Ticket.created_at < data_fim,
            )
            .count()
        )
        
        escalonamentos = (
            self.db.query(Ticket)
            .filter(
                Ticket.created_at >= data_inicio,
                Ticket.created_at < data_fim,
                Ticket.prioridade == "alta",
            )
            .count()
        )
        
        # Satisfação média
        conversas_com_satisfacao = (
            self.db.query(Conversa)
            .filter(
                Conversa.created_at >= data_inicio,
                Conversa.created_at < data_fim,
                Conversa.satisfacao.isnot(None),
            )
            .all()
        )
        
        if conversas_com_satisfacao:
            satisfacao_media = sum(c.satisfacao for c in conversas_com_satisfacao) / len(conversas_com_satisfacao)
            satisfacao_total = len(conversas_com_satisfacao)
        else:
            satisfacao_media = None
            satisfacao_total = 0
        
        return DadosMetricas(
            total_atendimentos=total_atendimentos,
            resolvidos_ia=resolvidos_ia,
            escalonamentos=escalonamentos,
            tickets_criados=tickets_criados,
            satisfacao_media=satisfacao_media,
            satisfacao_total=satisfacao_total,
            data=data_inicio,
        )
    
    def obter_temas_frequentes(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        limite: int = 5,
    ) -> list[dict]:
        """
        Obtém os temas mais frequentes das conversas.
        
        Args:
            data_inicio: Data de início
            data_fim: Data de fim
            limite: Número de temas a retornar
            
        Returns:
            Lista de dicionários com tema e contagem
        """
        if data_fim is None:
            data_fim = datetime.now()
        if data_inicio is None:
            data_inicio = data_fim - timedelta(days=7)
        
        # Por simplicidade, vamos contar as primeiras palavras das mensagens
        # Em uma implementação real, usaríamos NLP
        conversas = (
            self.db.query(Conversa.mensagem_usuario)
            .filter(
                Conversa.created_at >= data_inicio,
                Conversa.created_at < data_fim,
            )
            .all()
        )
        
        # Contagem simples de palavras
        from collections import Counter
        import re
        
        palavras_comuns = {"o", "a", "de", "que", "e", "do", "da", "em", "um", "para", "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "ao", "ele", "das", "à", "seu", "sua", "ou", "ser", "quando", "muito", "têm", "nos", "já", "eu", "também", "só", "pelo", "pela", "até", "isso", "ela", "entre", "depois", "sem", "mesmo", "aos", "seus", "meu", "minha", "tem", "à", "nao", "vc", "você", "ola", "oi", "bom", "dia"}
        
        contador = Counter()
        
        for conversa in conversas:
            if conversa.mensagem_usuario:
                palavras = re.findall(r'\b\w+\b', conversa.mensagem_usuario.lower())
                palavras_filtradas = [p for p in palavras if p not in palavras_comuns and len(p) > 3]
                contador.update(palavras_filtradas[:10])  # Limitar palavras por conversa
        
        temas = [{"tema": palavra, "quantidade": contagem} 
                 for palavra, contagem in contador.most_common(limite)]
        
        return temas


class ServicoRelatorios:
    """
    Serviço para gerar e enviar relatórios.
    """
    
    def __init__(self):
        """Inicializa o serviço de relatórios."""
        self.notificador = ServicoNotificacaoEquipe()
        self.metricas = ServicoMetricas()
    
    def formatar_dados_metrica(self, dados: DadosMetricas, titulo: str) -> str:
        """
        Formata os dados da métrica em uma mensagem.
        
        Args:
            dados: DadosMetricas
            titulo: Título do relatório
            
        Returns:
            String formatada
        """
        # Calcular taxa de resolução
        taxa_resolucao = 0
        if dados.total_atendimentos > 0:
            taxa_resolucao = (dados.resolvidos_ia / dados.total_atendimentos) * 100
        
        # Formatar satisfação
        satisfacao_str = "N/A"
        if dados.satisfacao_media is not None:
            satisfacao_str = f"{dados.satisfacao_media:.1f}/5 ({dados.satisfacao_total} avaliações)"
        
        # Emoji de satisfação
        if dados.satisfacao_media:
            if dados.satisfacao_media >= 4.5:
                emoji_satisfacao = "😁"
            elif dados.satisfacao_media >= 3.5:
                emoji_satisfacao = "🙂"
            elif dados.satisfacao_media >= 2.5:
                emoji_satisfacao = "😐"
            elif dados.satisfacao_media >= 1.5:
                emoji_satisfacao = "😕"
            else:
                emoji_satisfacao = "😞"
        else:
            emoji_satisfacao = "❓"
        
        mensagem = f"""📊 *{titulo}*

*Atendimentos:*
• Total: {dados.total_atendimentos}
• Resolvidos pela IA: {dados.resolvidos_ia} ({taxa_resolucao:.1f}%)
• Escalonamentos: {dados.escalonamentos}
• Tickets criados: {dados.tickets_criados}

*Satisfação:* {emoji_satisfacao} {satisfacao_str}

---
_Relatório automático do Sabiah_"""
        
        return mensagem
    
    async def enviar_relatorio_diario(self) -> bool:
        """
        Gera e envia o relatório diário.
        
        Returns:
            True se enviou com sucesso
        """
        logger.info("📊 Gerando relatório diário...")
        
        dados = self.metricas.obter_metricas_dia()
        mensagem = self.formatar_dados_metrica(dados, "Relatório Diário")
        
        # Adicionar temas frequentes
        temas = self.metricas.obter_temas_frequentes()
        if temas:
            temas_str = "\n".join([f"• {t['tema']} ({t['quantidade']})" for t in temas])
            mensagem += f"\n\n*Temas mais frequentes:*\n{temas_str}"
        
        # Enviar para equipe
        # TODO: Implementar envio assíncrono
        logger.info(f"📊 Relatório diário: {dados.total_atendimentos} atendimentos")
        
        return True
    
    async def enviar_relatorio_semanal(self) -> bool:
        """
        Gera e envia o relatório semanal.
        
        Returns:
            True se enviou com sucesso
        """
        logger.info("📊 Gerando relatório semanal...")
        
        hoje = datetime.now()
        data_inicio = hoje - timedelta(days=7)
        
        dados = self.metricas.obter_metricas_periodo(data_inicio, hoje)
        mensagem = self.formatar_dados_metrica(dados, "Relatório Semanal")
        
        # Adicionar comparação com semana anterior
        data_inicio_anterior = data_inicio - timedelta(days=7)
        dados_anterior = self.metricas.obter_metricas_periodo(data_inicio_anterior, data_inicio)
        
        if dados_anterior.total_atendimentos > 0:
            variacao = ((dados.total_atendimentos - dados_anterior.total_atendimentos) 
                       / dados_anterior.total_atendimentos * 100)
            
            emoji_variacao = "📈" if variacao > 0 else "📉" if variacao < 0 else "➡️"
            mensagem += f"\n\n*Variação vs semana anterior:* {emoji_variacao} {variacao:+.1f}%"
        
        # Adicionar temas frequentes
        temas = self.metricas.obter_temas_frequentes(data_inicio, hoje, 10)
        if temas:
            temas_str = "\n".join([f"• {t['tema']} ({t['quantidade']})" for t in temas])
            mensagem += f"\n\n*Temas mais frequentes:*\n{temas_str}"
        
        logger.info(f"📊 Relatório semanal: {dados.total_atendimentos} atendimentos")
        
        return True
    
    def agendar_relatorios(self) -> None:
        """
        Configura o agendamento de relatórios.
        
        TODO: Implementar com APScheduler ou similar
        """
        # Este método seria usado para agendar relatórios automáticos
        # Por exemplo, usando APScheduler:
        # scheduler.add_job(enviar_relatorio_diario, 'cron', hour=19, minute=0)
        # scheduler.add_job(enviar_relatorio_semanal, 'cron', day_of_week='monday', hour=9, minute=0)
        pass

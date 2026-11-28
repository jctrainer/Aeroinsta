# Ferramentas e conexões

| Ferramenta | Estado | Uso e limites |
|---|---|---|
| **PubMed** | ok | Toda checagem de ciência |
| **Windsor.ai** | conectado: Instagram (jotafit.personaltrainer), TikTok (jotafit), Google Meu Negócio (JOTA FIT) | Conta de teste: lê só os últimos 30 dias. Ações de escrita no Google (post, avaliação, perfil) só com ok do Jota |
| **Treinei (MT)** | conectado | Alunas, protocolos, planos vencendo, financeiro. **Só leitura** sem ordem do Jota |
| **ElevenLabs** | conectado | Imagem ≈ 190 créditos cada; vídeo IA 1.450 a 14.000 créditos por clipe; **sempre pedir aprovação por custo**. Não há clone da voz do Jota. Plano Starter (~39 mil caracteres/mês) |
| **Busca na web** | ok | Notícias e trends; conferir fonte original |
| Canva, Drive, Docs, Sheets, Gmail, OpusClip, TikTok for Business, HyperFrames | disponíveis | Usar quando a tarefa pedir |
| **Hostinger** | precisa autorização | O Jota autoriza em Configurações → Conectores no claude.ai |
| Skilldb, Krea, Instagram plugin, Slack e outros | bloqueados pela rede da sessão na nuvem ou desnecessários | Não depender deles |

## Ambiente
- Sessão na nuvem: não enxerga o computador do Jota nem a pasta ~/.codex (para isso, rodar o Claude Code localmente).
- Rede com proxy: alguns sites/serviços são bloqueados (o site jotafitpersonal.com.br não abre daqui).
- Área temporária da sessão (scratchpad) pode ser apagada; o que vale fica no repositório. Fotos de aluna e antes/depois **não** vão para o repositório.
- Repositório: jctrainer/aeroinsta, branch de trabalho `claude/analise-video-passada-040h9r`. Commit e push ao final de cada entrega; PR só se o Jota pedir.
- Skills úteis instaladas: social-media-skills (reels-script, hook-writer, caption-writer, content-calendar, instagram-seo, social-selling-and-dm, analytics-and-reporting), seo-local. Vídeos do Jota são feitos em CÓDIGO (Python + PIL/OpenCV + ffmpeg, scripts reels_v2.py etc.): Remotion e Motion Reel NUNCA foram usados e podem ficar desligados.


## Regra: conectores sob demanda (decisão do Jota, 28/11/2026; vale para TODOS os projetos)
Objetivo: economizar tokens, créditos e ruído. Cada conector/plugin ligado aumenta a lista de ferramentas e de skills que eu carrego a cada conversa.
- **Padrão:** só fica ligado o que a tarefa atual usa. Ao fim de cada entrega, eu aviso o que ficou sem uso.
- **Quem desliga:** o Jota, em claude.ai/customize/connectors (conectores) e nas configurações de plugins. Eu não consigo desligar daqui.
- **Para usar de novo:** leitura ou custo zero, eu conecto sozinho; gasta crédito (ElevenLabs, vídeo IA) ou mexe em conta externa (Google Meu Negócio, Instagram, site no ar), eu **peço permissão antes**.
- **Dica de economia:** nova conversa só com o necessário; conectores são lidos quando a conversa começa.

| Uso neste projeto | Conectores / plugins | O que fazer |
|---|---|---|
| **Usa sempre** | PubMed (ciência), GitHub (repositório), Playwright (local, já incluso) | Manter |
| **Usa de vez em quando** | Hostinger (site), Windsor.ai (Instagram, TikTok, Google Meu Negócio), Treinei/MT (alunas, só leitura), ElevenLabs (voz/imagem, gasta crédito), Canva | Ligar só no dia; pedir permissão se gastar ou editar conta |
| **Não usou até hoje** | Gmail, Google Docs/Sheets/Slides/Drive, HeyGen HyperFrames, OpusClip, TikTok for Business (anúncios), Clinical Trials, Claude Docs, Claude Academy, Desktop Commander | Candidatos a desligar |
| **Plugins sem relação com o negócio** | manufacturing, finance, carta-crm, product-management, marketing (Ahrefs, HubSpot, Klaviyo...), productivity (Slack, Notion...), animatedwebs, logo-maker, iMessage, Telegram, GitLab, BigQuery | Desligar |

- 28/11/2026: Jota desligou na conta os conectores/plugins sem uso (Clinical Trials, Gmail, Google Docs/Drive/Sheets/Slides, HyperFrames, OpusClip, TikTok for Business, GitLab e a maioria dos plugins). Mantidos: PubMed, GitHub nativo, Hostinger, Windsor.ai, MT, ElevenLabs, Canva (conferir se ficou ligado), social-media-skills, anthropic-skills.

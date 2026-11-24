# Jota Fit: padrões de conteúdo

Personal trainer, público majoritariamente feminino. Marca: amarelo sobre grafite, logo JF.
Todo conteúdo termina com o CTA da consultoria: **"Comenta CONSULTORIA que eu te chamo no direct"**.

## Equipe de agentes
O prompt master da equipe (agentes, perfis Jota Fit / NerdZoid / Razec Ezar, fluxo e comandos) está em `agentes/PROMPT-MASTER.md`. Siga-o em toda tarefa de conteúdo, marketing, vendas, site ou ciência do treino.

## REGRA Nº 1: base científica, sem erro, sempre revisada

Vale para TUDO: vídeos, legendas, títulos, capas, carrosséis, stories, roteiros, respostas e análises de treino.

1. **Buscar a base científica antes de escrever.** Todo dado, número, percentual, mecanismo ou recomendação de biomecânica, cinesiologia, fisiologia do exercício, nutrição esportiva ou saúde da mulher deve ser conferido no **PubMed** (ferramenta PubMed). Preferir meta-análises, revisões sistemáticas, ensaios randomizados e posicionamentos oficiais (ACSM, ISSN, PROT-AGE etc.).
2. **Sem erro.** Só entra o que a fonte realmente diz. Não confirmou? Sai do conteúdo ou é suavizado ("pode", "em média", "a pesquisa sugere"). Nunca inventar número, estudo, autor ou DOI. Não exagerar ("nunca", "sempre", "é genético/não é") além do que o estudo mostra.
3. **Revisão dupla obrigatória antes de entregar:**
   - Revisão 1, ciência: cada afirmação confrontada com a fonte (população do estudo, protocolo, tamanho do efeito, limites). Conferir se o estudo era com mulheres, idosos, treinadas etc. antes de generalizar.
   - Revisão 2, conteúdo: português correto, números consistentes entre slide/vídeo/legenda, textos dentro da área segura, nada cortado ou sobreposto, CTA presente.
4. **Registrar as fontes:** autor, ano, revista e DOI em `fontes.md` na pasta do projeto; no slide ou vídeo, citar no rodapé quando for o argumento central.
   **Toda legenda (Instagram, TikTok, Shorts) termina com "📚 Referências:"** em formato curto (Autor et al., ano, revista), antes das hashtags.
5. **Transparência:** imagens de IA ou montadas são "ilustração educativa"; gráficos esquemáticos são "ilustrativo"; temas clínicos levam "converse com seu médico".
6. **Ao entregar**, informar ao Jota o que foi conferido, o que foi corrigido e o que ficou de fora por falta de comprovação.
7. **Conteúdo de terceiros** (posts de referência, vídeos de outras professoras): analisar criticamente e apontar erros ou exageros com base na literatura, sem ataque pessoal.

## Carrossel JOTA FIT (padrão fixo)

Quando o Jota pedir "carrossel" (ou "carrossel JOTA FIT"), use SEMPRE este padrão, sem perguntar.

**Motor pronto:** `analises/carrosseis/scripts/carrossel.py` (fontes em `analises/carrosseis/fonts/`).
Exemplos completos: `scripts/c1.py` (músculo e longevidade) e `scripts/c2.py` (menopausa).
Copie um deles, troque o conteúdo e rode `python3 cX.py <pasta_saida>`.

**Visual**
- 1080×1350 (4:5), **7 slides** por padrão (capa, 4–5 de conteúdo, CTA).
- Fundo grafite `#0C0C0C` com leve brilho central e o **arco do "J"** em marca d'água à direita (`base()`); letra gigante opcional (`mark=`).
- Fonte **Poppins**: cabeçalho Bold com espaçamento largo, cinza `#9A9DA3`, no topo esquerdo (ex.: "CIÊNCIA JOTA FIT", "MÉTODO JOTA FIT", "TEMA · JOTA FIT"), e `n/7` à direita.
- **Kicker** amarelo `#F5C518` em caixa alta espaçada → **título** grande branco Poppins Bold (2 linhas) → **bullets com check amarelo** (`bullets()`, aceita `('Negrito:', 'resto')`) → **frase de impacto** amarela (`statement()`).
- Rodapé: **linha de progresso** amarela com círculo numerado no centro e o nome da etapa embaixo (`progress()`).
- Recursos: `chart()` (gráfico de linha em painel), `put_slice()` (imagem recortada com brilho), `tag()` (pílulas), `callout()` (setas com rótulo), `swipe()` ("Arrasta" + seta), `foot()` (fonte/citação pequena).
- Slide 7 = CTA: painel com "Comenta / **CONSULTORIA** / que eu te chamo no direct".
- Sem emoji dentro dos slides (Poppins não tem glifo de seta/emoji; desenhe setas).

**Conteúdo: base científica obrigatória**
- Fundamentar em **cinesiologia/biomecânica, fisiologia do exercício e educação física**, com linguagem simples para mulheres leigas.
- Todo número ou afirmação forte precisa ter base na literatura; citar o estudo no slide com `foot()` (autor, ano, revista) quando for o argumento central.
- **Checar cada dado no PubMed antes de entregar** (ferramenta PubMed): registrar autor, ano, revista e DOI em `fontes.md` da pasta do carrossel; o que não for confirmado sai do post ou é suavizado.
- Nunca inventar dado. Gráficos esquemáticos levam a marca **"ilustrativo"**.
- Imagens geradas por IA ou montadas são marcadas como **"ilustração educativa"**; nunca "imagem real".
- Corrigir mitos com contraponto (slide "Mito × Verdade" quando couber).
- Público feminino: priorizar exemplos de mulheres (inclusive 40+, menopausa) e linguagem de autonomia/saúde, não só estética.
- Para temas clínicos (osteoporose, menopausa, doenças), incluir "converse com seu médico".

**Entrega**
- Salvar em `analises/carrosseis/<tema>/` + `legendas.md` (legenda Instagram com hashtags, comentário fixado e ordem de postagem).
- Commit e push no branch de trabalho; enviar os PNGs ao Jota.

## Outros padrões já estabelecidos
- Capas de Reels/vídeo: `analises/capas/covers.py` (título sem caixa, branco + amarelo, espaço entre palavras e linhas; versão TikTok/Shorts com área segura).
- Vídeos: legendas sincronizadas palavra a palavra, círculo de rosto estilo react sem cobrir legenda/conteúdo, CTA da consultoria no fim, versões TikTok/Shorts com área segura.

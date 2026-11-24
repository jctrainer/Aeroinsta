# Jota Fit: padrões de conteúdo

Personal trainer, público majoritariamente feminino. Marca: amarelo sobre grafite, logo JF.
Todo conteúdo termina com o CTA da consultoria: **"Comenta CONSULTORIA que eu te chamo no direct"**.

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

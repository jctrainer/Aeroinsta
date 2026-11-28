# Padrão de carrossel: Método Jota Fit

Quando o Jota pedir "carrossel", usar SEMPRE este padrão, sem perguntar.

## Visual
- 1080×1350 (4:5), **7 slides**: capa, 4 a 5 de conteúdo, CTA.
- Fundo grafite `#0C0C0C` com leve brilho central e o arco do "J" em marca d'água; letra gigante opcional (`mark=`).
- Poppins. Cabeçalho Bold com espaçamento largo, cinza `#9A9DA3`, topo esquerdo ("CIÊNCIA JOTA FIT", "MÉTODO JOTA FIT", "SAÚDE DA MULHER · JOTA FIT", "MITO × VERDADE · JOTA FIT") e n/7 à direita.
- Kicker amarelo `#F5C518` em caixa alta espaçada → título branco grande (2 linhas) → bullets com check amarelo → frase de impacto amarela.
- Rodapé: linha de progresso amarela com círculo numerado no centro e nome da etapa embaixo.
- Slide 7 = CTA: painel "Comenta / **CONSULTORIA** / que eu te chamo no direct".
- Sem emoji dentro dos slides (Poppins não tem glifo); desenhe setas e ícones.
- **Sem marcas "ilustrativo" / "ilustração educativa"** (decisão do Jota). Fonte do estudo em rodapé pequeno quando for o argumento central.
- Foto de fundo com degradê (estilo do slide 3 da gestante) ficou mais bonito que foto em cartão: usar imagem como fundo com o lado do texto escuro.

## Carrossel infinito
Arte contínua de 7 × 1080 px fatiada em 7 slides: um elemento (foto, ✗, linha do gráfico) atravessa a divisa entre dois slides. Postar na ordem. Exemplo: ferramentas/carrossel/scripts/c4_metabolismo.py.

## Motores prontos (ferramentas/carrossel/scripts/)
carrossel.py (funções base) · c1 (músculo e longevidade) · c2 (menopausa) · c3_balanca · c4_metabolismo (infinito) · c5_gestante. Copiar um, trocar o conteúdo e rodar `python3 cX.py <saida> [<pasta_imagens>]`.

## Conteúdo
Cinesiologia/biomecânica, fisiologia do exercício e educação física, em linguagem simples. Todo número vem de estudo checado no PubMed (ver 07-ciencia-e-regras.md). Corrigir mitos com contraponto (Mito × Verdade). Exemplos com mulheres (inclusive 40+ e menopausa). Tema clínico: "converse com seu médico".

## Entrega
Pasta perfis/<perfil>/<pilar>/<tema>/ com slides + .zip em ordem + legenda.md + fontes.md (legenda com hashtags, comentário fixado e ordem de postagem). Commit e push; enviar os PNGs ao Jota.

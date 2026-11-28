# Padrão de vídeo (Reels, TikTok, Shorts)

## Estrutura A-roll + B-roll
- **A-roll** = Jota falando para a câmera (gancho, opinião, ironia, CTA). Sempre no 1º segundo e no final.
- **B-roll** = imagens de apoio sobre a voz: prioridade para **filmagem real** (treino dele, alunas com autorização escrita, execução, tela do app, comida, academia, ruas de Guarulhos). Banco em ferramentas/broll/ (README com a lista do que gravar; 20 clipes mínimos, vertical, 5 a 10 s). Imagem de IA só em exceção, nunca como aluna.
- Ritmo: troca de plano a cada 2 a 4 s; cada edição informa os clipes usados.
- **Edição leve** = sem efeito gratuito (transição chamativa, IA, enfeite). **Animações de biomecânica, anatomia e fisiologia são boas e necessárias** e entram sempre que ajudarem a explicar, sem limite fixo.

## Animações (referência: vídeo da passada)
Pontos de pose e linhas sobre o corpo; linha quadril–joelho–pé; arco do ângulo; músculo acendendo; câmera lenta no erro; medidas em tempo real; erros numerados; "como foi × como deveria"; checklist "o que eu faria"; contador de reps; cards de dado/comparação/gráfico; rosto de terceiros desfocado. Referências: perfis/jotafit/01-biomecanica-tecnica/passada-personal/ (principal), bulgaro, stiff e supino.

## Legenda na tela
- Sincronizada palavra a palavra. Versão "viral": 2 a 3 palavras grandes no centro, cada palavra "pula", palavras-chave em caixa amarela (METABOLISMO, MÚSCULO, CONSULTORIA...).
- Rodapé pequeno só com a **referência do estudo**. Sem "ilustrativo" / "ilustração educativa".

## Áudio
Voz do Jota (o ElevenLabs **não tem clone da voz dele**; ele gravou o áudio "JOTA_MT"); trilha leve gerada localmente (sem direitos autorais) que abaixa quando ele fala; "whoosh" nas trocas e "pop" nos carimbos; loudnorm em torno de -15 a -14 LUFS.

## Formatos e capas
- 1080×1920. Mesmo arquivo serve Reels, TikTok e Shorts, com **área segura** (nada nos ~140 px da direita nem embaixo, onde ficam botões e descrição).
- Capas: título sem caixa, branco + amarelo. Reels: conteúdo central cabe no recorte 3:4 da grade do perfil. TikTok/Shorts: versão com conteúdo deslocado à esquerda/cima. Motor: ferramentas/capas/covers.py.
- Círculo de rosto estilo react sem cobrir legenda nem cortar a testa.

## Série JOTA RESPONDE
Fundo grafite com brilho amarelo, botão "JOTA RESPONDE #nn", legenda palavra a palavra, zoom nas palavras-chave, cards com rosto em círculo, cards de ciência e CTA. Episódios 01 a 04 entregues (não reeditar); a partir do 05, A-roll + B-roll. Pasta: perfis/jotafit/07-jota-responde/.

## Motores (código)
- jr.py, mixjr.py, jrcover.py (JOTA RESPONDE), reels.py / reels_v2.py / capa_reels.py / capa_tiktok.py (perfis/jotafit/02-ciencia-e-mitos/mito-metabolismo-lento/scripts/). Recorte de fundo com MODNet, upscale Real-ESRGAN, transcrição faster-whisper, composição PIL/OpenCV + ffmpeg. A área temporária da sessão pode ser apagada: o que importa fica nas pastas do projeto.

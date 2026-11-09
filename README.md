# 🚀 Missão Espacial - Computação Gráfica 2D com OpenGL

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python) ![OpenGL](https://img.shields.io/badge/OpenGL-Core_Profile-5586A4?style=for-the-badge&logo=opengl) ![Status](https://img.shields.io/badge/Status-Concluído-success?style=for-the-badge)

Este repositório contém o projeto **Missão Espacial**, um mini jogo 2D interativo inspirado na estética de jogos 8-bit. O projeto foi desenvolvido como aplicação prática dos conceitos teóricos da disciplina de Computação Gráfica, utilizando a linguagem Python e a API gráfica OpenGL (Core Profile).

O motor gráfico foi construído do zero com foco em otimização, evitando o uso de bibliotecas de jogos prontas (como Pygame para renderização) e assumindo o controle direto da GPU através de Shaders personalizados em GLSL.

---

## 📸 A Jornada da Missão (Galeria do Projeto)

A simulação é controlada por uma Máquina de Estados Finitos (FSM) que avança pelas fases operacionais da missão antes de liberar o controle para o jogador.

### 1. Preparação e Ignição
O momento do disparo. A nave permanece na base enquanto o motor aciona o sistema de partículas dinâmicas para gerar a emissão inicial de fumaça.
> <img width="380" height="300" alt="image" src="https://github.com/user-attachments/assets/6806ab94-b4bc-4260-9d21-c6906b05c52e" />

### 2. Decolagem (Propulsão)
Animação do sprite sendo atualizada via coordenadas UV para exibir o fogo dos propulsores ativos enquanto a nave ganha aceleração.
> <img width="380" height="300" alt="image" src="https://github.com/user-attachments/assets/eacf42ab-ad9a-4b2a-b453-d76373a6417d" />

### 3. Voo Atmosférico
A ilusão de alta velocidade é criada pelo efeito de *parallax*, transladando o cenário de fundo (nuvens e solo procedural) no sentido inverso ao da nave.
> <img width="380" height="300" alt="image" src="https://github.com/user-attachments/assets/3b30785b-2690-48e3-a6b1-3958fc91a977" />

### 4. Desacoplamento de Estágios
O exato momento em que os tanques de combustível são ejetados. A lógica da aplicação atualiza instantaneamente o estado visual do sprite para a forma final da nave.
> <img width="380" height="300" alt="image" src="https://github.com/user-attachments/assets/ff47633e-ccc3-4d0f-826e-60d497648cf0" />


### 5. Transição Atmosférica (O Gradiente)
O céu não usa imagens de fundo; um shader procedural calcula um gradiente linear baseado na altitude para simular o escurecimento contínuo da atmosfera em direção ao vácuo espacial.
> <img width="380" height="300" alt="Gravando 2026-07-28 193821" src="https://github.com/user-attachments/assets/62b9ba35-b6a1-473f-8b8f-632e166016d4" />

### 6. Fase Espacial (O Jogo)
O momento em que a simulação vira um jogo interativo. O jogador assume o controle da nave em órbita para desviar de campos de asteroides e planetas gerados proceduralmente, com rotação e translação contínuas.
> <img width="380" height="300" alt="image" src="https://github.com/user-attachments/assets/d89e38ce-b427-4d70-8225-63f1263a1c04" />

### 7. HUD Customizado e Game Over
Tela final exibindo a barra de energia, o sistema de pontuação desenhado com primitivas geométricas (display de 7 segmentos) e o efeito de esmaecimento ao colidir.
> <img width="380" height="300" alt="Gravando 2026-07-28 195731" src="https://github.com/user-attachments/assets/bfa896a1-5d1e-44a5-81c4-282659fbcfba" />

---

## ⚙️ Principais Funcionalidades e Conceitos Técnicos

O desenvolvimento explorou a fundo a matemática gráfica e a comunicação CPU-GPU:

* **Transformações Geométricas Afins:** Aplicação intensa de Translação (para o efeito de *Parallax* e movimentação da nave), Rotação (inclinação da nave e órbita de asteroides) e Escala (expansão do sistema de partículas e elementos do HUD).
* **Animação por Coordenadas UV:** A nave não troca de textura na memória. A animação frame-a-frame é feita deslocando matematicamente as coordenadas da textura ($vUV=aUV*uEsc\_Tex+uDesl\_Tex;$) diretamente no Fragment Shader.
* **Texturização Procedural:** Nuvens, solo, grama, planetas e asteroides não são imagens carregadas de disco, mas sim padrões gerados proceduralmente em tempo de execução via ruído e sobreposição (usando a biblioteca Pillow).
* **Shaders Customizados (GLSL):**
  * *Shader Principal:* Gerencia objetos texturizados, transparência (Alpha Blending) e implementa a instrução `discard` para pixels totalmente transparentes.
  * *Shader do Céu:* Calcula gradientes lineares baseados na altitude (eixo Y) para realizar a transição dia/noite.
* **Física e Sistema de Partículas:** Implementação de movimento parabólico com aceleração gravitacional simulada, além de um sistema de exaustão do motor onde as partículas perdem opacidade (dissipação) e aumentam de tamanho com o tempo.

---

## 🛠️ Tecnologias Utilizadas

A arquitetura do motor foi construída sobre as seguintes ferramentas:

* **Linguagem & Core:** Python 3.12
* **Renderização:** PyOpenGL (Core Profile)
* **Matemática Vetorial:** PyGLM e NumPy
* **Criação de Texturas Procedurais:** Pillow (PIL)
* **Gerenciamento de Janelas e Contexto:** GLFW
* **Áudio (Streaming e SFX de baixa latência):** Pygame Mixer
* **Design de Sprites:** Piskel

---

## 🤖 Como Executar o Projeto

Certifique-se de ter o Python 3.12 instalado na sua máquina.

1. Clone este repositório:
   ```bash
   git clone https://github.com/SEU-USUARIO/Missao-Espacial.git
   cd Missao-Espacial
   
2. Crie e ative um ambiente virtual (recomendado):

   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
3. Instale as dependências necessárias:

   ```bash
   pip install -r requirements.txt
   
4. Execute o simulador:
   ```bash
   python main.py
   
## 👨‍💻 Autores
Projeto desenvolvido por:

| Nome                  |  GitHub                                             |
|-----------------------|-----------------------------------------------------|
| **Adry Oliveira**  |  [@elleoliveir](https://github.com/elleoliveir)     |
| **Filipe Corrêa**     |  [@Filipecorr34](https://github.com/Filipecorr34)   |

Desenvolvido para a disciplina de Computação Gráfica, ministrada pelo Prof. Dr. Fabrício Rossy.
   

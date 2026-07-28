import glm
from OpenGL.GL import *
import pygame
import os

# CONFIGURAÇÕES GLOBAIS
LARGURA, ALTURA = 800, 600
TEMPO_DECOLAGEM = 3.0

FASE_CENA    = 0
FASE_JOGO    = 1
FASE_DERROTA = 2

# ESTADO DO RENDERIZADOR
_textura_atual     = -1
_usa_textura_atual = -1

class Obj:
    __slots__ = ("posicao", "tamanho", "rotacao", "cor", "usa_textura", "textura_id", "esc_tex", "desl_tex", "alfa")
    def __init__(self, posicao, tamanho, rotacao=0.0, cor=None, usa_textura=False, textura_id=0, esc_tex=None, desl_tex=None, alfa=1.0):
        self.posicao = posicao
        self.tamanho = tamanho
        self.rotacao = rotacao
        self.cor = cor if cor is not None else glm.vec4(1, 1, 1, 1)
        self.usa_textura = usa_textura
        self.textura_id = textura_id
        self.esc_tex = esc_tex if esc_tex is not None else glm.vec2(1, 1)
        self.desl_tex = desl_tex if desl_tex is not None else glm.vec2(0, 0)
        self.alfa = alfa

class Particula:
    __slots__ = ("posicao", "velocidade", "vida", "vida_maxima", "tamanho", "cor", "tipo")
    def __init__(self, posicao, velocidade, vida, tamanho, cor, tipo="fumaca"):
        self.posicao = glm.vec2(posicao)
        self.velocidade = glm.vec2(velocidade)
        self.vida = vida
        self.vida_maxima = vida
        self.tamanho = tamanho
        self.cor = cor
        self.tipo = tipo

def visivel(obj, margem=80):
    metade_l, metade_a = obj.tamanho.x / 2 + margem, obj.tamanho.y / 2 + margem
    return not (obj.posicao.x + metade_l < 0 or obj.posicao.x - metade_l > LARGURA or obj.posicao.y + metade_a < 0 or obj.posicao.y - metade_a > ALTURA)

def desenhar(VAO, obj, loc_uniformes):
    global _textura_atual, _usa_textura_atual
    if not visivel(obj): return
    matriz_modelo = glm.mat4(1.0)
    matriz_modelo = glm.translate(matriz_modelo, glm.vec3(obj.posicao.x, obj.posicao.y, 0))
    if obj.rotacao != 0.0: matriz_modelo = glm.rotate(matriz_modelo, glm.radians(obj.rotacao), glm.vec3(0, 0, 1))
    matriz_modelo = glm.scale(matriz_modelo, glm.vec3(obj.tamanho.x, obj.tamanho.y, 1))
    
    glUniformMatrix4fv(loc_uniformes["modelo"], 1, GL_FALSE, glm.value_ptr(matriz_modelo))
    glUniform4f(loc_uniformes["cor"], obj.cor.x, obj.cor.y, obj.cor.z, obj.cor.w)
    glUniform1f(loc_uniformes["alfa"], obj.alfa)
    
    usa_tex_int = int(obj.usa_textura)
    if _usa_textura_atual != usa_tex_int:
        glUniform1i(loc_uniformes["usa_tex"], usa_tex_int)
        _usa_textura_atual = usa_tex_int
        
    if obj.usa_textura:
        glUniform2fv(loc_uniformes["esc_tex"], 1, glm.value_ptr(obj.esc_tex))
        glUniform2fv(loc_uniformes["desl_tex"], 1, glm.value_ptr(obj.desl_tex))
        if _textura_atual != obj.textura_id:
            glBindTexture(GL_TEXTURE_2D, obj.textura_id)
            _textura_atual = obj.textura_id
    else:
        if _textura_atual != 0:
            glBindTexture(GL_TEXTURE_2D, 0)
            _textura_atual = 0
            
    glBindVertexArray(VAO)
    glDrawArrays(GL_TRIANGLES, 0, 6)

# ── GESTÃO DE ÁUDIO (PYGAME) ──
def inicializar_audio():
    try:
        pygame.mixer.init()
    except Exception as erro:
        print(f"[ERRO] Falha ao iniciar mixer de áudio: {erro}")

def carregar_som(nome_arquivo, volume=0.5):
    """Carrega um SFX garantindo que ele busque na pasta 'audios'"""
    caminho = os.path.join("audios", nome_arquivo)
    try:
        som = pygame.mixer.Sound(caminho)
        som.set_volume(volume)
        return som
    except Exception as e:
        print(f"[AVISO] Áudio não encontrado: {caminho}")
        return None

def tocar_musica_fundo(nome_arquivo, volume=1.0):
    """Vigilante da música ambiente: só toca se estiver em silêncio"""
    caminho = os.path.join("audios", nome_arquivo)
    try:
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
    except Exception:
        pass

def parar_musica_fundo():
    try:
        pygame.mixer.music.stop()
    except:
        pass
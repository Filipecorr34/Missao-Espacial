import glfw
from OpenGL.GL import *
import glm
import numpy as np
import ctypes, math, random
import pygame

# Importação dos nossos módulos Customizados
from motor import LARGURA, ALTURA, TEMPO_DECOLAGEM, FASE_CENA, FASE_JOGO, FASE_DERROTA
from motor import Obj, Particula, desenhar, inicializar_audio, carregar_som, tocar_musica_fundo, parar_musica_fundo
from shaders import compilar_shaders
import texturas

ARQUIVOS_TANQUE = [
    "tanque.png", "tanque10.png", "tanque20.png", "tanque30.png",
    "tanque40.png", "tanque50.png", "tanque60.png", "tanque70.png",
    "tanque80.png", "tanque90.png", "tanque100.png"
]

class CenaLancamento:
    def __init__(self):
        gerador = random.Random(42)
        # Texturas geradas para a cena (ou carregadas de arquivos em imagens/)
        self.tex_grama = texturas.gerar_grama()
        self.tex_nuvem = texturas.gerar_nuvem()
        self.tex_estrela = texturas.gerar_estrela()
        self.tex_plataforma = texturas.gerar_plataforma()
        self.tex_torre = texturas.gerar_torre()
        self.tex_fumaca = texturas.gerar_fumaca()
        self.tex_sol = texturas.gerar_sol_corona()
        self.tex_decolando = texturas.carregar_png("FogueteDecolando1.png")
        self.tex_voando = texturas.carregar_png("FogueteVOO.png")
        self.tex_desacoplando = texturas.carregar_png("FogueteDesacoplando.png")
        
        # Áudio de Lançamento (o motor busca em audios/)
        self.som_lancamento = carregar_som("som_lancamento.mp3", 0.7)

        self.fase_cena = 0
        self.tempo = 0.0
        self.tempo_segurando = 0.0
        self.tempo_decolagem = 0.0
        self.quadro_animacao = 0.0
        self.vel_animacao = 12.0
        self.estado_sprite = 0
        self.tempo_voo_sprite = 0.0
        self.rolagem_y = 0.0
        self.fator_noite = 0.0
        self.alfa_esmaecimento = 0.0
        self.concluida = False

        self.ceu_topo = glm.vec3(0.22, 0.52, 0.93)
        self.ceu_base = glm.vec3(0.58, 0.78, 1.00)

        self.estrelas = []
        for _ in range(200):
            ex = gerador.uniform(0, LARGURA); ey = gerador.uniform(-1400, 0)
            tam = gerador.uniform(2.5, 5.5); bri = gerador.uniform(0.6, 1.0)
            self.estrelas.append(Obj(glm.vec2(ex, ey), glm.vec2(tam, tam), cor=glm.vec4(bri, bri, bri * .9, 1), usa_textura=True, textura_id=self.tex_estrela))

        self.posicao_sol = glm.vec2(100, 80)
        self.corona_sol = Obj(self.posicao_sol, glm.vec2(120, 120), cor=glm.vec4(1, 1, 1, 1), usa_textura=True, textura_id=self.tex_sol)
        self.raios_sol = []
        for angulo in range(0, 360, 20):
            self.raios_sol.append(Obj(self.posicao_sol, glm.vec2(5, 130), rotacao=float(angulo), cor=glm.vec4(1.0, 0.88, 0.2, 0.18)))

        self.nuvens = []
        camadas = [(100, glm.vec2(180, 72), 0.25, 0.96), (210, glm.vec2(130, 52), 0.45, 0.82), (310, glm.vec2(95, 40), 0.65, 0.65)]
        for y, tamanho, velocidade, alfa in camadas:
            for _ in range(4):
                x = gerador.uniform(-60, LARGURA + 60)
                self.nuvens.append({"objeto": Obj(glm.vec2(x, y), tamanho, cor=glm.vec4(1, 1, 1, 1), usa_textura=True, textura_id=self.tex_nuvem, alfa=alfa), "velocidade": velocidade})

        self.chao = Obj(glm.vec2(LARGURA / 2, 574), glm.vec2(LARGURA * 3, 130), cor=glm.vec4(1, 1, 1, 1), usa_textura=True, textura_id=self.tex_grama, esc_tex=glm.vec2(6, 1))
        self.sombra_chao = Obj(glm.vec2(LARGURA / 2, 510), glm.vec2(LARGURA * 3, 22), cor=glm.vec4(0.04, 0.12, 0.04, 0.65))
        self.plataforma = Obj(glm.vec2(LARGURA / 2, 498), glm.vec2(270, 20), cor=glm.vec4(1, 1, 1, 1), usa_textura=True, textura_id=self.tex_plataforma, esc_tex=glm.vec2(4, 1))
        self.torres = [
            Obj(glm.vec2(514, 368), glm.vec2(30, 300), usa_textura=True, textura_id=self.tex_torre, esc_tex=glm.vec2(1, 9)),
            Obj(glm.vec2(469, 262), glm.vec2(88, 12), cor=glm.vec4(0.52, 0.09, 0.09, 1)),
            Obj(glm.vec2(469, 362), glm.vec2(88, 12), cor=glm.vec4(0.52, 0.09, 0.09, 1)),
        ]
        self.luz_torre = Obj(glm.vec2(514, 214), glm.vec2(10, 10), cor=glm.vec4(1, 0.1, 0.1, 1))

        self.nave = Obj(glm.vec2(LARGURA / 2, 392), glm.vec2(500, 500), rotacao=180.0, cor=glm.vec4(1, 1, 1, 1), usa_textura=True, textura_id=self.tex_decolando if self.tex_decolando else 0, esc_tex=glm.vec2(1 / 16, 1))

        self.particulas = []
        self.tempo_emissao = 0.0

        self.tex_fundo_barra = texturas.gerar_barra_hud(204, 18)
        self.tex_preenchimento_barra = texturas.gerar_barra_combustivel(196, 12, 0.0)
        self.pct_barra = 0.0

    def limpar_memoria_gpu(self):
        texturas_para_apagar = [
            self.tex_grama, self.tex_nuvem, self.tex_estrela, self.tex_plataforma, 
            self.tex_torre, self.tex_fumaca, self.tex_sol, 
            self.tex_decolando, self.tex_voando, self.tex_desacoplando
        ]
        texturas_validas = [t for t in texturas_para_apagar if t != 0]
        if texturas_validas:
            glDeleteTextures(len(texturas_validas), texturas_validas)

    def _emitir_fumaca_base(self, delta_tempo, intensa=False):
        self.tempo_emissao -= delta_tempo
        if self.tempo_emissao > 0: return
        qtd = 6 if intensa else 3
        self.tempo_emissao = 0.02 if intensa else 0.04
        base_x = self.nave.posicao.x; base_y = self.nave.posicao.y + self.nave.tamanho.y * 0.35
        for _ in range(qtd):
            vx = random.uniform(-18, 18); vy = random.uniform(25, 70)
            vida = random.uniform(1.5, 3.2); tamanho = random.uniform(25, 65)
            g = random.uniform(0.55, 0.82)
            self.particulas.append(Particula((base_x + random.uniform(-18, 18), base_y), (vx, vy), vida, tamanho, glm.vec4(g, g, g, 0.75), "fumaca"))
        if intensa:
            for _ in range(4):
                angulo = random.uniform(0, math.pi * 2); velocidade = random.uniform(30, 90)
                self.particulas.append(Particula((base_x + random.uniform(-8, 8), base_y + 5), (math.cos(angulo) * velocidade, math.sin(angulo) * velocidade), random.uniform(0.3, 0.8), random.uniform(6, 14), glm.vec4(1.0, random.uniform(0.4, 0.8), 0.0, 1.0), "faisca"))

    def _emitir_fumaca_voo(self, delta_tempo):
        self.tempo_emissao -= delta_tempo
        if self.tempo_emissao > 0: return
        self.tempo_emissao = 0.03
        bx = self.nave.posicao.x; by = self.nave.posicao.y + self.nave.tamanho.y * 0.35
        for _ in range(4):
            vx = random.uniform(-12, 12); vy = random.uniform(30, 80)
            vida = random.uniform(1.8, 3.5); tamanho = random.uniform(30, 70)
            g = random.uniform(0.5, 0.78)
            self.particulas.append(Particula((bx + random.uniform(-15, 15), by), (vx, vy), vida, tamanho, glm.vec4(g, g, g * 1.05, 0.65), "fumaca"))

    def _atualizar_particulas(self, delta_tempo):
        vivos = []
        for p in self.particulas:
            p.vida -= delta_tempo
            if p.vida <= 0: continue
            p.posicao.x += p.velocidade.x * delta_tempo; p.posicao.y += p.velocidade.y * delta_tempo
            p.velocidade.x *= 0.97
            if p.tipo == "fumaca":
                p.tamanho += 14 * delta_tempo
                t = 1 - (p.vida / p.vida_maxima)
                p.cor.w = 0.65 * (1 - t * t)
            else:
                p.velocidade.y += 120 * delta_tempo
                t = 1 - (p.vida / p.vida_maxima)
                p.cor.w = 1.0 - t
            vivos.append(p)
        self.particulas = vivos

    def processar_tecla(self, tecla, acao):
        if tecla == glfw.KEY_SPACE:
            if acao == glfw.PRESS and self.fase_cena in (0, 1):
                self.fase_cena = 1
                if self.som_lancamento: self.som_lancamento.play()
            elif acao == glfw.RELEASE and self.fase_cena == 1:
                if self.som_lancamento: self.som_lancamento.fadeout(500)

    def atualizar(self, delta_tempo, teclas):
        self.tempo += delta_tempo

        for raio in self.raios_sol:
            raio.rotacao += 7 * delta_tempo; raio.posicao = self.posicao_sol
        self.corona_sol.posicao = self.posicao_sol

        if self.fase_cena == 1:
            if teclas.get(glfw.KEY_SPACE, False):
                self.tempo_segurando += delta_tempo
                self.pct_barra = min(1.0, self.tempo_segurando / TEMPO_DECOLAGEM)
                intensidade = self.tempo_segurando / TEMPO_DECOLAGEM
                self.tempo_emissao -= delta_tempo
                if self.tempo_emissao <= 0:
                    qtd = int(4 + intensidade * 8)
                    self.tempo_emissao = max(0.01, 0.05 - intensidade * 0.03)
                    bx = self.nave.posicao.x; by = self.nave.posicao.y + self.nave.tamanho.y * 0.20
                    for _ in range(qtd):
                        vx = random.uniform(-20, 20) * intensidade; vy = random.uniform(20, 60) + intensidade * 40
                        vida = random.uniform(1.5, 3.5); tamanho = random.uniform(20, 55 + intensidade * 30)
                        g = random.uniform(0.5, 0.82)
                        self.particulas.append(Particula((bx + random.uniform(-20, 20), by), (vx, vy), vida, tamanho, glm.vec4(g, g, g, 0.8), "fumaca"))
                    if intensidade > 0.6:
                        for _ in range(int(intensidade * 5)):
                            angulo = random.uniform(0, math.pi * 2); vel = random.uniform(40, 100)
                            self.particulas.append(Particula((bx + random.uniform(-10, 10), by + 5), (math.cos(angulo) * vel, math.sin(angulo) * vel), random.uniform(0.2, 0.6), random.uniform(5, 12), glm.vec4(1.0, random.uniform(0.3, 0.7), 0.0, 1.0), "faisca"))
                if self.tempo_segurando >= TEMPO_DECOLAGEM:
                    self.fase_cena = 2; self.tempo_decolagem = 0.0; self.quadro_animacao = 0.0
            else:
                self.tempo_segurando = max(0, self.tempo_segurando - delta_tempo * 0.8)
                self.pct_barra = self.tempo_segurando / TEMPO_DECOLAGEM
                if self.tempo_segurando == 0: self.fase_cena = 0

        elif self.fase_cena == 2:
            self.tempo_decolagem += delta_tempo
            self.quadro_animacao += self.vel_animacao * delta_tempo

            if self.estado_sprite == 0:
                if self.quadro_animacao >= 16:
                    self.estado_sprite = 1; self.quadro_animacao = 0
                    if self.tex_voando: self.nave.textura_id = self.tex_voando
                    self.nave.esc_tex = glm.vec2(1/6, 1); self.nave.desl_tex = glm.vec2(0, 0)
                    self.torres[1].posicao.x += 38; self.torres[2].posicao.x += 38
                    self.nave.posicao.x = LARGURA / 2
                else:
                    fi = int(self.quadro_animacao) % 16
                    self.nave.desl_tex = glm.vec2(fi * self.nave.esc_tex.x, 0)
            elif self.estado_sprite == 1:
                self.tempo_voo_sprite += delta_tempo
                fi = int(self.quadro_animacao) % 6
                self.nave.desl_tex = glm.vec2(fi * self.nave.esc_tex.x, 0)
                if self.tempo_voo_sprite > 5.0:
                    self.estado_sprite = 2; self.quadro_animacao = 0
                    if self.tex_desacoplando: self.nave.textura_id = self.tex_desacoplando
                    self.nave.esc_tex = glm.vec2(1/23, 1); self.nave.desl_tex = glm.vec2(0, 0)
            elif self.estado_sprite == 2:
                fi = int(self.quadro_animacao) if self.quadro_animacao < 23 else 21 + int(self.quadro_animacao - 23) % 2
                self.nave.desl_tex = glm.vec2(fi * self.nave.esc_tex.x, 0)

            if self.estado_sprite > 0:
                vel = 100 * delta_tempo
                if self.nave.posicao.y > ALTURA / 2:
                    self.nave.posicao.y -= vel
                else:
                    self.rolagem_y += vel
                    for obj in [self.chao, self.sombra_chao, self.plataforma] + self.torres + [self.luz_torre]:
                        obj.posicao.y += vel
                    for nc in self.nuvens:
                        nc["objeto"].posicao.y += vel * nc["velocidade"] * 1.5
                    for s in [self.corona_sol] + self.raios_sol:
                        s.posicao.y += vel * 0.07
                    self.posicao_sol.y += vel * 0.07

                for e in self.estrelas:
                    e.posicao.y += vel * 0.4
                    if e.posicao.y > ALTURA + 20:
                        e.posicao.y = random.uniform(-100, -10); e.posicao.x = random.uniform(0, LARGURA)

                self.fator_noite = min(1.0, self.rolagem_y / 700.0)
                self._emitir_fumaca_voo(delta_tempo)

                if self.rolagem_y > 1200:
                    self.alfa_esmaecimento = min(1.0, self.alfa_esmaecimento + delta_tempo * 0.8)
                    if self.alfa_esmaecimento >= 1.0:
                        self.concluida = True
            else:
                self.nave.posicao.x = (LARGURA / 2) + random.uniform(-1.5, 1.5)
                self._emitir_fumaca_base(delta_tempo, intensa=True)

        self._atualizar_particulas(delta_tempo)

        if self.fase_cena == 1 and self.pct_barra != getattr(self, "_ultima_pct", None):
            self._ultima_pct = self.pct_barra
            if self.tex_preenchimento_barra: glDeleteTextures(1, [self.tex_preenchimento_barra])
            self.tex_preenchimento_barra = texturas.gerar_barra_combustivel(196, 12, self.pct_barra)

        piscar = 0.5 + 0.5 * math.sin(self.tempo * 4.5)
        self.luz_torre.cor = glm.vec4(1.0, 0.05, 0.05, piscar)

    def renderizar(self, VAO, prog_ceu, loc_uniformes_ceu, prog_principal, loc_uniformes_princ):
        glUseProgram(prog_ceu)
        glUniform3fv(loc_uniformes_ceu["topo"], 1, glm.value_ptr(self.ceu_topo))
        glUniform3fv(loc_uniformes_ceu["base"], 1, glm.value_ptr(self.ceu_base))
        glUniform1f(loc_uniformes_ceu["noite"], self.fator_noite)
        glUniform1f(loc_uniformes_ceu["tempo"], self.tempo)
        glBindVertexArray(VAO); glDrawArrays(GL_TRIANGLES, 0, 6)
        glUseProgram(prog_principal)

        if self.fator_noite > 0.05:
            for e in self.estrelas:
                e.alfa = self.fator_noite; desenhar(VAO, e, loc_uniformes_princ)

        alfa_sol = max(0.0, 1.0 - self.fator_noite * 1.4)
        self.corona_sol.alfa = alfa_sol
        desenhar(VAO, self.corona_sol, loc_uniformes_princ)
        for raio in self.raios_sol:
            raio.alfa = alfa_sol * 0.5; desenhar(VAO, raio, loc_uniformes_princ)

        alfa_nuvem = max(0.0, 1.0 - self.fator_noite * 1.2)
        for nc in self.nuvens:
            nc["objeto"].alfa = alfa_nuvem; desenhar(VAO, nc["objeto"], loc_uniformes_princ)

        desenhar(VAO, self.sombra_chao, loc_uniformes_princ)
        desenhar(VAO, self.chao, loc_uniformes_princ)
        desenhar(VAO, self.plataforma, loc_uniformes_princ)
        for t in self.torres: desenhar(VAO, t, loc_uniformes_princ)
        desenhar(VAO, self.luz_torre, loc_uniformes_princ)

        for p in self.particulas:
            if p.tipo == "fumaca":
                po = Obj(p.posicao, glm.vec2(p.tamanho, p.tamanho), cor=p.cor, usa_textura=True, textura_id=self.tex_fumaca, alfa=p.cor.w)
            else:
                po = Obj(p.posicao, glm.vec2(p.tamanho, p.tamanho), cor=p.cor, alfa=p.cor.w)
            desenhar(VAO, po, loc_uniformes_princ)

        desenhar(VAO, self.nave, loc_uniformes_princ)

        if self.fase_cena in (0, 1):
            larg_b = 204; alt_b = 18; bx = LARGURA / 2; by = ALTURA - 42
            fundo_b = Obj(glm.vec2(bx, by), glm.vec2(larg_b + 6, alt_b + 6), cor=glm.vec4(0, 0, 0, 0.7), alfa=0.7)
            desenhar(VAO, fundo_b, loc_uniformes_princ)
            fundo2_b = Obj(glm.vec2(bx, by), glm.vec2(larg_b, alt_b), usa_textura=True, textura_id=self.tex_fundo_barra, alfa=0.9)
            desenhar(VAO, fundo2_b, loc_uniformes_princ)
            if self.pct_barra > 0:
                larg_p = 196 * self.pct_barra
                preenchimento = Obj(glm.vec2(bx - 98 + larg_p / 2, by), glm.vec2(larg_p, 12), usa_textura=True, textura_id=self.tex_preenchimento_barra, alfa=0.95)
                desenhar(VAO, preenchimento, loc_uniformes_princ)
            pulsacao = 0.7 + 0.3 * math.sin(self.tempo * 3)
            fundo_dica = Obj(glm.vec2(LARGURA / 2, ALTURA - 68), glm.vec2(240, 20), cor=glm.vec4(0, 0, 0, pulsacao * 0.5), alfa=pulsacao * 0.5)
            desenhar(VAO, fundo_dica, loc_uniformes_princ)

        if self.alfa_esmaecimento > 0:
            esmaecimento = Obj(glm.vec2(LARGURA / 2, ALTURA / 2), glm.vec2(LARGURA + 4, ALTURA + 4), cor=glm.vec4(0, 0, 0, 1), alfa=self.alfa_esmaecimento)
            desenhar(VAO, esmaecimento, loc_uniformes_princ)


class MiniJogo:
    def __init__(self):
        gerador = random.Random(7)
        self.tex_estrela = texturas.gerar_estrela()
        self.tex_fumaca = texturas.gerar_fumaca()
        self.tex_foguete = texturas.carregar_png("Foguete.png")
        self.tex_impulso = texturas.carregar_png("FogueteImpulso.png")
        self.tex_esf_azul = texturas.gerar_esfera(0.2, 0.5, 1.0)
        self.tex_esf_verm = texturas.gerar_esfera(1.0, 0.15, 0.15)
        self.tex_tanques = [texturas.carregar_png(p) for p in ARQUIVOS_TANQUE]
        self.tex_asteroides = [texturas.gerar_asteroide(32, 32, i) for i in range(5)]
        self.tex_planetas = [texturas.gerar_planeta(96, 96, i) for i in range(4)]

        self.som_explosao = carregar_som("explosao.mp3", 0.5)
        self.som_azul = carregar_som("azul.mp3", 0.5)
        self.som_verm = carregar_som("verm.mp3", 0.5)
        self.som_impulso = carregar_som("impulso.mp3", 0.4)
        
        try:
            self.canal_impulso = pygame.mixer.Channel(2)
        except:
            self.canal_impulso = None

        self.combustivel = 1.0
        self.impulso = False
        self.derrotado = False
        self.tempo = 0.0
        self.esmaecimento_entrada = 1.0
        self.vel_base_rolagem = 120.0
        self.score = 0
        self.distancia = 0.0

        self.posicao_nave = glm.vec2(LARGURA / 2, ALTURA * 0.65)
        self.inclinacao_nave = 0.0
        self.rotacao_base_nave = 180.0
        self.tempo_anim_fogo = 0.0

        self.estrelas = []
        for _ in range(250):
            ex = gerador.uniform(0, LARGURA); ey = gerador.uniform(0, ALTURA)
            tam = gerador.uniform(2, 5); bri = gerador.uniform(0.5, 1.0)
            self.estrelas.append({"objeto": Obj(glm.vec2(ex, ey), glm.vec2(tam, tam), cor=glm.vec4(bri, bri, bri * .9, 1), usa_textura=True, textura_id=self.tex_estrela), "velocidade": gerador.uniform(0.3, 1.0)})

        self.obstaculos = []
        self.coletaveis = []
        self.tempo_geracao = 0.0
        self._gerar_iniciais(gerador)

        self.particulas = []
        self.tempo_emissao = 0.0

        self.tex_fundo_barra = texturas.gerar_barra_hud(204, 18)
        self.tex_barra_combustivel = texturas.gerar_barra_combustivel(196, 12, 1.0)
        self.nebulosas = self._gerar_nebulosas(gerador)

    def limpar_memoria_gpu(self):
        texturas_para_apagar = [self.tex_estrela, self.tex_fumaca, self.tex_foguete, self.tex_impulso, self.tex_esf_azul, self.tex_esf_verm, self.tex_fundo_barra, self.tex_barra_combustivel] + self.tex_tanques + self.tex_asteroides + self.tex_planetas
        texturas_validas = [t for t in texturas_para_apagar if t != 0]
        if texturas_validas:
            glDeleteTextures(len(texturas_validas), texturas_validas)

    def _gerar_nebulosas(self, gerador):
        nbs = []
        for _ in range(5):
            x = gerador.uniform(0, LARGURA); y = gerador.uniform(0, ALTURA)
            largura_n = gerador.uniform(120, 280); altura_n = gerador.uniform(80, 180)
            r = gerador.uniform(0.3, 0.8); g = gerador.uniform(0.1, 0.4); b = gerador.uniform(0.5, 1.0)
            a = gerador.uniform(0.03, 0.09)
            nbs.append(Obj(glm.vec2(x, y), glm.vec2(largura_n, altura_n), cor=glm.vec4(r, g, b, a), alfa=a))
        return nbs

    def _gerar_iniciais(self, gerador):
        for i in range(6): self._gerar_obstaculo(y_inicial=gerador.uniform(-400, -50))
        for i in range(4): self._gerar_coletavel(y_inicial=gerador.uniform(-400, -50))

    def _gerar_obstaculo(self, y_inicial=None):
        tipo = random.choice(["ast", "ast", "ast", "plan"])
        if tipo == "ast":
            tam = random.uniform(40, 75); tex = random.choice(self.tex_asteroides)
        else:
            tam = random.uniform(90, 140); tex = random.choice(self.tex_planetas)
        x = random.uniform(tam, LARGURA - tam)
        y = y_inicial if y_inicial is not None else random.uniform(-150, -tam)
        vel = random.uniform(60, 130)
        self.obstaculos.append({
            "posicao": glm.vec2(x, y), "tamanho": glm.vec2(tam, tam),
            "tipo": tipo, "textura_id": tex, "velocidade": vel,
            "rotacao": random.uniform(0, 360), "vel_rotacao": random.uniform(-30, 30)
        })

    def _gerar_coletavel(self, y_inicial=None):
        tipo = random.choice(["azul", "azul", "verm"])
        tex = self.tex_esf_azul if tipo == "azul" else self.tex_esf_verm
        x = random.uniform(20, LARGURA - 20)
        y = y_inicial if y_inicial is not None else random.uniform(-120, -20)
        self.coletaveis.append({
            "posicao": glm.vec2(x, y), "tamanho": glm.vec2(26, 26),
            "tipo": tipo, "textura_id": tex, "velocidade": random.uniform(50, 90),
            "pulsacao": 0.0
        })

    def _atualizar_barra_combustivel(self):
        if self.tex_barra_combustivel: glDeleteTextures(1, [self.tex_barra_combustivel])
        self.tex_barra_combustivel = texturas.gerar_barra_combustivel(196, 12, max(0, self.combustivel))

    def _emitir_fumaca(self, delta_tempo, impulso=False, vel_lateral=0.0):
        self.tempo_emissao -= delta_tempo
        if self.tempo_emissao > 0: return
        self.tempo_emissao = 0.015 if impulso else 0.04
        ang_rad = math.radians(self.inclinacao_nave)
        dist_turbina = 30 
        bx = self.posicao_nave.x - math.sin(ang_rad) * dist_turbina
        by = self.posicao_nave.y + math.cos(ang_rad) * dist_turbina
        qtd_particulas = 5 if impulso else 2
        
        for i in range(qtd_particulas):
            forca_motor = random.uniform(300, 500) if impulso else random.uniform(100, 180)
            vx_motor = math.sin(ang_rad) * forca_motor
            vy_motor = math.cos(ang_rad) * forca_motor
            vx = vx_motor + (vel_lateral * 0.3) + random.uniform(-15, 15)
            vy = vy_motor + random.uniform(-10, 30)
            vida = random.uniform(0.5, 1.2)
            tamanho_p = random.uniform(15, 30)
            if impulso and i < 2:
                cor = glm.vec4(1.0, random.uniform(0.5, 0.9), 0.1, 1.0)
                tipo = "fogo"
            else:
                g = random.uniform(0.4, 0.7)
                cor = glm.vec4(g, g, g, 0.8)
                tipo = "fumaca"
            self.particulas.append(Particula((bx + random.uniform(-10, 10), by + random.uniform(-5, 5)), (vx, vy), vida, tamanho_p, cor, tipo))

    def _atualizar_particulas(self, delta_tempo):
        vivos = []
        for p in self.particulas:
            p.vida -= delta_tempo
            if p.vida <= 0: continue
            p.posicao.x += p.velocidade.x * delta_tempo
            p.posicao.y += p.velocidade.y * delta_tempo
            p.velocidade.x *= 0.92
            p.velocidade.y *= 0.95
            t = 1.0 - (p.vida / p.vida_maxima)
            if p.tipo == "fumaca":
                p.tamanho += 35 * delta_tempo
                p.cor.w = 0.7 * (1.0 - t)
            elif p.tipo == "fogo":
                p.tamanho += 5 * delta_tempo
                p.cor.y = max(0.0, p.cor.y - 2.5 * delta_tempo)
                p.cor.w = 1.0 - (t * t)
            vivos.append(p)
        self.particulas = vivos

    def processar_tecla(self, tecla, acao):
        if acao == glfw.PRESS and tecla == glfw.KEY_SPACE: self.impulso = True
        if acao == glfw.RELEASE and tecla == glfw.KEY_SPACE: self.impulso = False

    def atualizar(self, delta_tempo, teclas):
        if self.derrotado: return
        self.tempo += delta_tempo
        if self.esmaecimento_entrada > 0: self.esmaecimento_entrada = max(0, self.esmaecimento_entrada - delta_tempo * 1.5)

        self.tempo_anim_fogo += delta_tempo * 15.0

        fator = 2.5 if (self.impulso and self.combustivel > 0) else 1.0
        vel_rolagem = self.vel_base_rolagem * fator * delta_tempo

        if self.impulso and self.combustivel > 0:
            self.combustivel = max(0, self.combustivel - 0.015 * delta_tempo * 60)
            self._atualizar_barra_combustivel()
            if self.som_impulso and self.canal_impulso and not self.canal_impulso.get_busy():
                self.canal_impulso.play(self.som_impulso, loops=-1)
        else:
            self.impulso = False
            if hasattr(self, 'canal_impulso') and self.canal_impulso and self.canal_impulso.get_busy():
                self.canal_impulso.stop()

        vel_nave = 160 * delta_tempo * (1.5 if self.impulso else 1.0)
        alvo_inclinacao = 0.0
        vel_lateral = 0.0 

        if teclas.get(glfw.KEY_LEFT, False):
            self.posicao_nave.x = max(40, self.posicao_nave.x - vel_nave)
            alvo_inclinacao = -45.0   
            vel_lateral = -vel_nave / delta_tempo

        if teclas.get(glfw.KEY_RIGHT, False):
            self.posicao_nave.x = min(LARGURA - 40, self.posicao_nave.x + vel_nave)
            alvo_inclinacao = 45.0   
            vel_lateral = vel_nave / delta_tempo

        if teclas.get(glfw.KEY_UP, False):
            self.posicao_nave.y = max(60, self.posicao_nave.y - vel_nave)
        if teclas.get(glfw.KEY_DOWN, False):
            self.posicao_nave.y = min(ALTURA - 60, self.posicao_nave.y + vel_nave)
            
        self.inclinacao_nave += (alvo_inclinacao - self.inclinacao_nave) * 8 * delta_tempo
        self.distancia += vel_rolagem * (2.5 if self.impulso else 1.0)

        for e in self.estrelas:
            e["objeto"].posicao.y += vel_rolagem * e["velocidade"] * 0.5
            if e["objeto"].posicao.y > ALTURA + 10:
                e["objeto"].posicao.y = random.uniform(-30, -5)
                e["objeto"].posicao.x = random.uniform(0, LARGURA)

        for nb in self.nebulosas:
            nb.posicao.y += vel_rolagem * 0.2
            if nb.posicao.y > ALTURA + 200: nb.posicao.y = random.uniform(-200, -50)

        for o in self.obstaculos:
            o["posicao"].y += vel_rolagem + o["velocidade"] * delta_tempo
            o["rotacao"] += o["vel_rotacao"] * delta_tempo
        self.obstaculos = [o for o in self.obstaculos if o["posicao"].y < ALTURA + 200]
        
        self.tempo_geracao += delta_tempo
        if self.tempo_geracao > random.uniform(0.8, 1.8):
            self.tempo_geracao = 0; self._gerar_obstaculo()
            if random.random() < 0.5: self._gerar_coletavel()

        for c in self.coletaveis:
            c["posicao"].y += vel_rolagem + c["velocidade"] * delta_tempo
            c["pulsacao"] += delta_tempo * 3
        self.coletaveis = [c for c in self.coletaveis if c["posicao"].y < ALTURA + 100]

        raio_nave = 30  
        for o in self.obstaculos[:]:
            r = o["tamanho"].x * 0.38
            dx = self.posicao_nave.x - o["posicao"].x; dy = self.posicao_nave.y - o["posicao"].y
            if math.sqrt(dx * dx + dy * dy) < raio_nave + r:
                if self.som_explosao: self.som_explosao.play()
                self.derrotado = True; return
                
        novos_coletaveis = []
        for c in self.coletaveis:
            r = c["tamanho"].x * 0.5
            dx = self.posicao_nave.x - c["posicao"].x; dy = self.posicao_nave.y - c["posicao"].y
            if math.sqrt(dx * dx + dy * dy) < raio_nave + r:
                if c["tipo"] == "azul":
                    if self.som_azul: self.som_azul.play()
                    ganho = 0.10; self.score += 10
                else:
                    if self.som_verm: self.som_verm.play()
                    ganho = 0.25; self.score += 25
                
                self.combustivel = min(1.0, self.combustivel + ganho)
                self._atualizar_barra_combustivel()
            else:
                novos_coletaveis.append(c)
        self.coletaveis = novos_coletaveis

        self._emitir_fumaca(delta_tempo, self.impulso, vel_lateral)
        self._atualizar_particulas(delta_tempo)

    def renderizar(self, VAO, prog_ceu, loc_uniformes_ceu, prog_principal, loc_uniformes_princ):
        glUseProgram(prog_ceu)
        glUniform3fv(loc_uniformes_ceu["topo"], 1, glm.value_ptr(glm.vec3(0.0, 0.0, 0.02)))
        glUniform3fv(loc_uniformes_ceu["base"], 1, glm.value_ptr(glm.vec3(0.01, 0.0, 0.04)))
        glUniform1f(loc_uniformes_ceu["noite"], 1.0)
        glUniform1f(loc_uniformes_ceu["tempo"], self.tempo)
        glBindVertexArray(VAO); glDrawArrays(GL_TRIANGLES, 0, 6)
        glUseProgram(prog_principal)

        for nb in self.nebulosas: desenhar(VAO, nb, loc_uniformes_princ)
        for e in self.estrelas:
            e["objeto"].alfa = 1.0; desenhar(VAO, e["objeto"], loc_uniformes_princ)

        for o in self.obstaculos:
            if o["tipo"] == "plan":
                obj = Obj(o["posicao"], o["tamanho"], rotacao=o["rotacao"], usa_textura=True, textura_id=o["textura_id"])
                desenhar(VAO, obj, loc_uniformes_princ)

        for c in self.coletaveis:
            pulsacao_tam = 1.0 + 0.1 * math.sin(c["pulsacao"])
            tamanho_c = glm.vec2(c["tamanho"].x * pulsacao_tam, c["tamanho"].y * pulsacao_tam)
            obj = Obj(c["posicao"], tamanho_c, usa_textura=True, textura_id=c["textura_id"])
            desenhar(VAO, obj, loc_uniformes_princ)

        for o in self.obstaculos:
            if o["tipo"] == "ast":
                obj = Obj(o["posicao"], o["tamanho"], rotacao=o["rotacao"], usa_textura=True, textura_id=o["textura_id"])
                desenhar(VAO, obj, loc_uniformes_princ)

        for p in self.particulas:
            po = Obj(p.posicao, glm.vec2(p.tamanho, p.tamanho), cor=p.cor, usa_textura=True, textura_id=self.tex_fumaca, alfa=p.cor.w)
            desenhar(VAO, po, loc_uniformes_princ)

        rotacao_total = self.rotacao_base_nave + self.inclinacao_nave
        usando_impulso = self.impulso and self.combustivel > 0
        tex_atual = self.tex_impulso if usando_impulso else self.tex_foguete
        num_quadros = 16 if usando_impulso else 3 
        
        if tex_atual:
            esc_x = 1.0 / num_quadros
            quadro = int(self.tempo_anim_fogo) % num_quadros
            desl_x = quadro * esc_x
            
            nobj = Obj(self.posicao_nave, glm.vec2(110, 110), rotacao=rotacao_total, usa_textura=True, textura_id=tex_atual, esc_tex=glm.vec2(esc_x, 1), desl_tex=glm.vec2(desl_x, 0))
        else:
            nobj = Obj(self.posicao_nave, glm.vec2(60, 80), rotacao=rotacao_total, cor=glm.vec4(0.8, 0.8, 0.9, 1))
        
        desenhar(VAO, nobj, loc_uniformes_princ)

        idx_tanque = min(10, max(0, round(self.combustivel * 10)))
        tex_tanque_atual = self.tex_tanques[idx_tanque]
        if tex_tanque_atual:
            obj_tanque = Obj(glm.vec2(LARGURA - 55, ALTURA - 110), glm.vec2(64, 154), rotacao=180.0, usa_textura=True, textura_id=tex_tanque_atual)
            desenhar(VAO, obj_tanque, loc_uniformes_princ)

        bx = LARGURA / 2; by = ALTURA - 22
        fundo_barra = Obj(glm.vec2(bx, by), glm.vec2(210, 24), cor=glm.vec4(0, 0, 0, 0.7), alfa=0.7)
        desenhar(VAO, fundo_barra, loc_uniformes_princ)
        fundo2_barra = Obj(glm.vec2(bx, by), glm.vec2(204, 18), usa_textura=True, textura_id=self.tex_fundo_barra, alfa=0.9)
        desenhar(VAO, fundo2_barra, loc_uniformes_princ)
        if self.combustivel > 0:
            largura_p = 196 * self.combustivel
            preenchimento_barra = Obj(glm.vec2(bx - 98 + largura_p / 2, by), glm.vec2(largura_p, 12), usa_textura=True, textura_id=self.tex_barra_combustivel, alfa=0.95)
            desenhar(VAO, preenchimento_barra, loc_uniformes_princ)

        if self.impulso and self.combustivel > 0:
            destaque_visual = Obj(glm.vec2(LARGURA / 2, ALTURA / 2), glm.vec2(LARGURA, ALTURA), cor=glm.vec4(0.0, 0.2, 1.0, 0.04), alfa=0.04)
            desenhar(VAO, destaque_visual, loc_uniformes_princ)

        if self.esmaecimento_entrada > 0:
            esmaecimento_ent = Obj(glm.vec2(LARGURA / 2, ALTURA / 2), glm.vec2(LARGURA + 4, ALTURA + 4), cor=glm.vec4(0, 0, 0, 1), alfa=self.esmaecimento_entrada)
            desenhar(VAO, esmaecimento_ent, loc_uniformes_princ)

class TelaDerrota:
    def __init__(self, distancia: float, score: int):
        self.tempo = 0.0
        self.esmaecimento = 0.0
        
        self.alfa_explosao = 1.0 
        self.alfa_reiniciar = 0.0
        self.reiniciando = False
        
        self.distancia_km = int(distancia / 50)
        self.score = score
        
        self.texturas_digitos = [texturas.gerar_digito(i) for i in range(10)]
        self.tex_painel = self._gerar_painel()
        self.tex_linha = self._gerar_separador()
        
        self.tex_titulo = texturas.gerar_texto_retro("NAVE DESTRUiDA", (255, 60, 60, 255))
        self.tex_btn = texturas.gerar_texto_retro("PRESSIONE  R  PARA REINICIAR", (200, 200, 200, 255))
        self.tex_dist = texturas.gerar_texto_retro("DISTANCIA", (100, 200, 255, 255))
        self.tex_pts = texturas.gerar_texto_retro("PONTOS ", (255, 220, 50, 255))
        self.tex_km = texturas.gerar_texto_retro("KM", (100, 200, 255, 255))

    def limpar_memoria_gpu(self):
        texturas_para_apagar = self.texturas_digitos + [
            self.tex_painel, self.tex_linha, self.tex_titulo, 
            self.tex_btn, self.tex_dist, self.tex_pts, self.tex_km
        ]
        texturas_validas = [t for t in texturas_para_apagar if t != 0]
        if texturas_validas:
            glDeleteTextures(len(texturas_validas), texturas_validas)

    def _gerar_painel(self, largura=400, altura=280) -> int:
        from PIL import Image, ImageDraw
        import numpy as np
        img = Image.new("RGBA", (largura, altura), (0,0,0,0)); desenho = ImageDraw.Draw(img)
        for y in range(altura):
            t = y / altura
            r = int(80 - t * 30); g = int(5); b = int(5)
            desenho.line([(0, y), (largura, y)], fill=(r, g, b, 200))
        for x in range(largura):
            desenho.point((x, 0), (200, 30, 30, 255)); desenho.point((x, altura - 1), (200, 30, 30, 255))
        for y in range(altura):
            desenho.point((0, y), (200, 30, 30, 255)); desenho.point((largura - 1, y), (200, 30, 30, 255))
        for x in range(2, largura - 2):
            desenho.point((x, 2), (150, 20, 20, 200)); desenho.point((x, altura - 3), (150, 20, 20, 200))
        for y in range(2, altura - 2):
            desenho.point((2, y), (150, 20, 20, 200)); desenho.point((largura - 3, y), (150, 20, 20, 200))
        for cx, cy in [(0, 0), (largura - 8, 0), (0, altura - 8), (largura - 8, altura - 8)]:
            desenho.rectangle([cx, cy, cx + 7, cy + 7], fill=(220, 40, 40, 255))
        return texturas.carregar_rgba_gpu(np.array(img, dtype=np.uint8))

    def _gerar_separador(self, largura=360, altura=3) -> int:
        from PIL import Image, ImageDraw
        import numpy as np
        img = Image.new("RGBA", (largura, altura), (0,0,0,0)); desenho = ImageDraw.Draw(img)
        for x in range(0, largura, 4):
            desenho.line([(x, 1), (x + 2, 1)], fill=(180, 40, 40, 200))
        return texturas.carregar_rgba_gpu(np.array(img, dtype=np.uint8))

    def _desenhar_numero(self, VAO, loc_uniformes, numero: int, cx: float, cy: float, largura_d=18, altura_d=26, espacamento=4, cor_n=None):
        digitos = [int(d) for d in str(max(0, numero))]
        largura_total = len(digitos) * (largura_d + espacamento) - espacamento
        inicio_x = cx - largura_total / 2 + largura_d / 2
        for i, d in enumerate(digitos):
            tex_digito = self.texturas_digitos[d]
            cor_final = cor_n if cor_n else glm.vec4(0.3, 0.9, 0.3, 1)
            obj = Obj(glm.vec2(inicio_x + i * (largura_d + espacamento), cy), glm.vec2(largura_d, altura_d), usa_textura=True, textura_id=tex_digito, cor=cor_final, alfa=self.esmaecimento)
            desenhar(VAO, obj, loc_uniformes)

    def atualizar(self, delta_tempo):
        self.tempo += delta_tempo
        self.esmaecimento = min(1.0, self.esmaecimento + delta_tempo * 1.4)
        
        if self.alfa_explosao > 0:
            self.alfa_explosao = max(0.0, self.alfa_explosao - delta_tempo * 1.5)
            
        if self.reiniciando:
            self.alfa_reiniciar += delta_tempo * 2.5

    def renderizar(self, VAO, prog_principal, loc_uniformes_princ):
        glUseProgram(prog_principal)
        pulsacao = 0.85 + 0.15 * math.sin(self.tempo * 3.5)

        camada_escura = Obj(glm.vec2(LARGURA / 2, ALTURA / 2), glm.vec2(LARGURA, ALTURA), cor=glm.vec4(0, 0, 0, 1), alfa=0.82 * self.esmaecimento)
        desenhar(VAO, camada_escura, loc_uniformes_princ)

        painel_y = ALTURA / 2 - 10
        painel = Obj(glm.vec2(LARGURA / 2, painel_y), glm.vec2(400, 280), usa_textura=True, textura_id=self.tex_painel, alfa=self.esmaecimento)
        desenhar(VAO, painel, loc_uniformes_princ)

        titulo = Obj(glm.vec2(LARGURA / 2, ALTURA / 2 - 110), glm.vec2(280, 35), usa_textura=True, textura_id=self.tex_titulo, alfa=self.esmaecimento)
        desenhar(VAO, titulo, loc_uniformes_princ)

        separador1 = Obj(glm.vec2(LARGURA / 2, ALTURA / 2 - 75), glm.vec2(360, 3), usa_textura=True, textura_id=self.tex_linha, alfa=self.esmaecimento)
        desenhar(VAO, separador1, loc_uniformes_princ)

        texto_dist = Obj(glm.vec2(LARGURA / 2 - 80, ALTURA / 2 - 35), glm.vec2(130, 20), usa_textura=True, textura_id=self.tex_dist, alfa=self.esmaecimento)
        desenhar(VAO, texto_dist, loc_uniformes_princ)
        self._desenhar_numero(VAO, loc_uniformes_princ, self.distancia_km, cx=LARGURA / 2 + 50, cy=ALTURA / 2 - 35, cor_n=glm.vec4(0.4, 0.85, 1.0, 1))
        texto_km = Obj(glm.vec2(LARGURA / 2 + 115, ALTURA / 2 - 32), glm.vec2(30, 15), usa_textura=True, textura_id=self.tex_km, alfa=self.esmaecimento)
        desenhar(VAO, texto_km, loc_uniformes_princ)

        separador2 = Obj(glm.vec2(LARGURA / 2, ALTURA / 2), glm.vec2(360, 3), usa_textura=True, textura_id=self.tex_linha, alfa=self.esmaecimento)
        desenhar(VAO, separador2, loc_uniformes_princ)

        texto_pts = Obj(glm.vec2(LARGURA / 2 - 80, ALTURA / 2 + 35), glm.vec2(100, 20), usa_textura=True, textura_id=self.tex_pts, alfa=self.esmaecimento)
        desenhar(VAO, texto_pts, loc_uniformes_princ)
        self._desenhar_numero(VAO, loc_uniformes_princ, self.score, cx=LARGURA / 2 + 50, cy=ALTURA / 2 + 35, cor_n=glm.vec4(1.0, 0.88, 0.2, 1))

        btn_restart = Obj(glm.vec2(LARGURA / 2, ALTURA / 2 + 95), glm.vec2(280, 20), usa_textura=True, textura_id=self.tex_btn, alfa=pulsacao * self.esmaecimento)
        desenhar(VAO, btn_restart, loc_uniformes_princ)

        if self.alfa_explosao > 0:
            flash = Obj(glm.vec2(LARGURA / 2, ALTURA / 2), glm.vec2(LARGURA, ALTURA), cor=glm.vec4(1, 1, 1, 1), alfa=self.alfa_explosao)
            desenhar(VAO, flash, loc_uniformes_princ)
            
        if self.alfa_reiniciar > 0:
            fade_restart = Obj(glm.vec2(LARGURA / 2, ALTURA / 2), glm.vec2(LARGURA, ALTURA), cor=glm.vec4(0, 0, 0, 1), alfa=self.alfa_reiniciar)
            desenhar(VAO, fade_restart, loc_uniformes_princ)


def main():
    if not glfw.init(): raise RuntimeError("GLFW falhou")
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    janela = glfw.create_window(LARGURA, ALTURA, "Missao Espacial", None, None)
    if not janela: glfw.terminate(); return
    glfw.make_context_current(janela)
    glfw.swap_interval(1)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_DEPTH_TEST)
    
    inicializar_audio()

    prog_principal, prog_ceu = compilar_shaders()

    vertices = np.array([
        -0.5,-0.5, 0.0,0.0,  0.5,-0.5, 1.0,0.0,  -0.5,0.5, 0.0,1.0,
         0.5,-0.5, 1.0,0.0,  0.5, 0.5, 1.0,1.0,  -0.5,0.5, 0.0,1.0,
    ], dtype=np.float32)
    VAO = glGenVertexArrays(1); VBO = glGenBuffers(1)
    glBindVertexArray(VAO); glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    tamanho_vertice = 4 * 4
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, tamanho_vertice, ctypes.c_void_p(0)); glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, tamanho_vertice, ctypes.c_void_p(8)); glEnableVertexAttribArray(1)

    loc_uniformes_ceu = {
        "topo":  glGetUniformLocation(prog_ceu, "uCeuTopo"),
        "base":  glGetUniformLocation(prog_ceu, "uCeuBase"),
        "noite": glGetUniformLocation(prog_ceu, "uNoite"),
        "tempo": glGetUniformLocation(prog_ceu, "uTempo"),
    }
    
    glUseProgram(prog_principal)
    projecao = glm.ortho(0.0, float(LARGURA), float(ALTURA), 0.0, -1.0, 1.0)
    glUniformMatrix4fv(glGetUniformLocation(prog_principal, "uProjecao"), 1, GL_FALSE, glm.value_ptr(projecao))
    
    loc_uniformes_princ = {
        "modelo":   glGetUniformLocation(prog_principal, "uModelo"),
        "cor":      glGetUniformLocation(prog_principal, "uCor"),
        "usa_tex":  glGetUniformLocation(prog_principal, "uUsaTextura"),
        "esc_tex":  glGetUniformLocation(prog_principal, "uEscTex"),
        "desl_tex": glGetUniformLocation(prog_principal, "uDeslTex"),
        "alfa":     glGetUniformLocation(prog_principal, "uAlfa"),
    }

    fase = FASE_CENA
    cena = CenaLancamento()
    jogo = None
    derrota = None

    teclas = {}
    def ao_pressionar_tecla(janela_atual, tecla, scan, acao, mods):
        nonlocal fase, jogo, derrota
        if acao == glfw.PRESS:   teclas[tecla] = True
        if acao == glfw.RELEASE: teclas[tecla] = False
        if tecla == glfw.KEY_ESCAPE and acao == glfw.PRESS:
            glfw.set_window_should_close(janela_atual, True)
            
        if fase == FASE_CENA:
            cena.processar_tecla(tecla, acao)
        elif fase == FASE_JOGO and jogo:
            jogo.processar_tecla(tecla, acao)
            
        if fase == FASE_DERROTA and tecla == glfw.KEY_R and acao == glfw.PRESS:
            if derrota: 
                derrota.reiniciando = True

    glfw.set_key_callback(janela, ao_pressionar_tecla)

    tempo0 = glfw.get_time()

    while not glfw.window_should_close(janela):
        tempo1 = glfw.get_time(); delta_tempo = min(tempo1 - tempo0, 0.05); tempo0 = tempo1
        glClear(GL_COLOR_BUFFER_BIT)

        if fase == FASE_CENA:
            cena.atualizar(delta_tempo, teclas)
            cena.renderizar(VAO, prog_ceu, loc_uniformes_ceu, prog_principal, loc_uniformes_princ)
            if cena.concluida:
                if cena.som_lancamento:
                    cena.som_lancamento.fadeout(1000)

                cena.limpar_memoria_gpu()
                fase = FASE_JOGO; jogo = MiniJogo()

        elif fase == FASE_JOGO and jogo:
            tocar_musica_fundo("musica_fundo.mp3", 0.5)

            jogo.atualizar(delta_tempo, teclas)
            jogo.renderizar(VAO, prog_ceu, loc_uniformes_ceu, prog_principal, loc_uniformes_princ)
            if jogo.derrotado:
                parar_musica_fundo()
                if hasattr(jogo, 'canal_impulso') and jogo.canal_impulso:
                    jogo.canal_impulso.stop()

                fase = FASE_DERROTA
                derrota = TelaDerrota(distancia=jogo.distancia, score=jogo.score)

        elif fase == FASE_DERROTA:
            if jogo: jogo.renderizar(VAO, prog_ceu, loc_uniformes_ceu, prog_principal, loc_uniformes_princ)
            derrota.atualizar(delta_tempo)
            derrota.renderizar(VAO, prog_principal, loc_uniformes_princ)
            
            if derrota.reiniciando and derrota.alfa_reiniciar >= 1.0:
                derrota.limpar_memoria_gpu()
                jogo.limpar_memoria_gpu()
                fase = FASE_JOGO
                jogo = MiniJogo()
                derrota = None

        glfw.swap_buffers(janela)
        glfw.poll_events()

    if cena: cena.limpar_memoria_gpu()
    if jogo: jogo.limpar_memoria_gpu()
    if derrota: derrota.limpar_memoria_gpu()
    glfw.terminate()

if __name__ == "__main__":
    main()
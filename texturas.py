import numpy as np
from PIL import Image, ImageDraw
import math, random, os
from OpenGL.GL import *

def carregar_rgba_gpu(arr: np.ndarray, suave_nearest=True) -> int:
    altura_img, largura_img = arr.shape[:2]
    id_textura = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, id_textura)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    filtro = GL_NEAREST if suave_nearest else GL_LINEAR
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, filtro)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, filtro)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, largura_img, altura_img, 0, GL_RGBA, GL_UNSIGNED_BYTE, arr.tobytes())
    return id_textura

def carregar_png(nome_arquivo) -> int:
    """Busca o arquivo automaticamente na pasta 'imagens'"""
    caminho = os.path.join("imagens", nome_arquivo)
    try:
        imagem = Image.open(caminho).transpose(Image.FLIP_TOP_BOTTOM).convert("RGBA")
        return carregar_rgba_gpu(np.array(imagem, dtype=np.uint8))
    except Exception as erro:
        print(f"[AVISO] Imagem não carregada: '{caminho}': {erro}")
        return 0

def gerar_texto_retro(texto, cor=(255, 255, 255, 255)) -> int:
    largura = len(texto) * 6 + 4
    altura = 12
    img = Image.new("RGBA", (largura, altura), (0,0,0,0))
    desenho = ImageDraw.Draw(img)
    desenho.text((2, 1), texto, fill=cor) 
    return carregar_rgba_gpu(np.array(img, dtype=np.uint8))

def gerar_grama(largura=256, altura=80) -> int:
    gerador = random.Random(42)
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); desenho = ImageDraw.Draw(img)
    for y in range(altura):
        t = y / altura
        r = int(55 + t * 35); g = int(95 + t * 25); b = int(28 + t * 12)
        desenho.line([(0, y), (largura, y)], fill=(r, g, b, 255))
    for _ in range(60):
        sx = gerador.randint(0, largura - 5); sy = gerador.randint(altura - 22, altura - 4); sc = gerador.randint(90, 150)
        desenho.ellipse([sx, sy, sx + gerador.randint(3, 7), sy + gerador.randint(2, 4)], fill=(sc, sc, sc - 8, 255))
    paleta = [(75,155,45,255), (55,130,35,255), (95,175,55,255), (45,110,30,255), (115,195,65,255), (90,170,50,255)]
    for _ in range(largura * 5):
        bx = gerador.randint(0, largura - 4); bh = gerador.randint(5, 16); bw = gerador.randint(2, 4)
        c = gerador.choice(paleta)
        for px in range(bw):
            for py in range(bh):
                yy = altura - 22 - py
                if 0 <= yy < altura and 0 <= bx + px < largura:
                    cor = (min(255, c[0]+25), min(255, c[1]+25), c[2], 255) if py == bh-1 else c
                    img.putpixel((bx + px, yy), cor)
    return carregar_rgba_gpu(np.array(img, dtype=np.uint8))

def gerar_nuvem(largura=128, altura=64) -> int:
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); desenho = ImageDraw.Draw(img)
    sombra = (140, 150, 175, 170)
    for cx, cy, rx, ry in [(68,30,30,16), (88,34,18,12), (52,34,18,12), (70,40,38,13)]:
        desenho.ellipse([cx-rx+5, cy-ry+7, cx+rx+5, cy+ry+7], fill=sombra)
    for cx, cy, rx, ry in [(68,27,31,17), (88,31,21,15), (52,31,21,15), (70,37,38,15)]:
        desenho.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=(225, 232, 245, 255))
    for cx, cy, rx, ry in [(64,20,21,11), (84,24,13,9), (53,24,13,9)]:
        desenho.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=(255, 255, 255, 255))
    desenho.ellipse([32, 40, 108, 58], fill=(170, 182, 205, 255))
    img_pequena = img.resize((largura//4, altura//4), Image.NEAREST)
    return carregar_rgba_gpu(np.array(img_pequena.resize((largura, altura), Image.NEAREST), dtype=np.uint8))

def gerar_estrela() -> int:
    img = Image.new("RGBA", (8, 8), (0,0,0,0))
    img.putpixel((3, 3), (255, 255, 215, 255)); img.putpixel((4, 3), (255, 255, 220, 255))
    img.putpixel((3, 4), (255, 255, 220, 255)); img.putpixel((4, 4), (255, 255, 255, 255))
    img.putpixel((3, 2), (200, 200, 180, 160)); img.putpixel((4, 5), (200, 200, 180, 160))
    return carregar_rgba_gpu(np.array(img, dtype=np.uint8))

def gerar_plataforma(largura=64, altura=16) -> int:
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); desenho = ImageDraw.Draw(img)
    for y in range(altura):
        t = y / altura; c = int(75 + t * 45)
        desenho.line([(0, y), (largura, y)], fill=(c, c, c + 12, 255))
    for bx in [3, 14, 50, 61]:
        desenho.rectangle([bx, 3, bx + 3, 7], fill=(175, 180, 200, 255))
    desenho.line([(0, altura//2), (largura, altura//2)], fill=(50, 52, 72, 255))
    desenho.line([(0, altura - 1), (largura, altura - 1)], fill=(40, 40, 60, 255))
    return carregar_rgba_gpu(np.array(img, dtype=np.uint8))

def gerar_torre(largura=18, altura=128) -> int:
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); desenho = ImageDraw.Draw(img)
    for y in range(altura):
        t = y / altura; c = int(95 - t * 35)
        desenho.line([(0, y), (largura, y)], fill=(c, c, c + 18, 255))
    for y in range(0, altura, 10):
        desenho.line([(0, y), (largura, y)], fill=(45, 45, 65, 255))
    for y in range(altura):
        t = y / altura; c = int(45 - t * 18)
        desenho.line([(largura - 5, y), (largura, y)], fill=(c, c, c, 210))
    for y in range(0, altura, 10):
        for x in range(2, largura - 2, 3):
            if (x // 3 + y // 10) % 2 == 0: desenho.point((x, y), fill=(110, 110, 130, 255))
    return carregar_rgba_gpu(np.array(img, dtype=np.uint8))

def gerar_fumaca(largura=64, altura=64) -> int:
    img = Image.new("RGBA", (largura, altura), (0,0,0,0))
    cx, cy = largura // 2, altura // 2
    for y in range(altura):
        for x in range(largura):
            dx, dy = x - cx, y - cy; r = math.sqrt(dx * dx + dy * dy); raio_max = min(largura, altura) / 2.0
            if r < raio_max:
                t = (1.0 - r / raio_max) ** 1.8; c = int(165 + t * 55); a = int(t * 190)
                img.putpixel((x, y), (c, c, c + 5, a))
    img_pequena = img.resize((largura//4, altura//4), Image.NEAREST)
    return carregar_rgba_gpu(np.array(img_pequena.resize((largura, altura), Image.NEAREST), dtype=np.uint8))

def gerar_sol_corona(largura=128, altura=128) -> int:
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); cx = cy = largura // 2
    for y in range(altura):
        for x in range(largura):
            dx, dy = x - cx, y - cy; r = math.sqrt(dx * dx + dy * dy)
            if r < 48:
                brilho = 1.0 - r / 48.0; a = 255
                img.putpixel((x, y), (255, int(230 + brilho * 25), int(brilho * 180), a))
            elif r < 60:
                t = (r - 48) / 12.0; a = int((1 - t) * 220)
                img.putpixel((x, y), (255, 200, 60, a))
            elif r < largura // 2:
                t = (r - 60) / (largura // 2 - 60); a = int((1 - t) ** 2 * 100)
                img.putpixel((x, y), (255, 160, 20, a))
    img_pequena = img.resize((largura//4, altura//4), Image.NEAREST)
    return carregar_rgba_gpu(np.array(img_pequena.resize((largura, altura), Image.NEAREST), dtype=np.uint8))

def gerar_asteroide(largura=32, altura=32, semente=0) -> int:
    gerador = random.Random(semente)
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); cx = cy = largura // 2
    pontos = []
    for i in range(12):
        angulo = i * 2 * math.pi / 12; r = cx * (0.6 + gerador.random() * 0.4)
        pontos.append((int(cx + r * math.cos(angulo)), int(cy + r * math.sin(angulo))))
    desenho = ImageDraw.Draw(img)
    c1 = (gerador.randint(90, 130), gerador.randint(80, 110), gerador.randint(60, 90))
    desenho.polygon(pontos, fill=(*c1, 255))
    for _ in range(3):
        cr = gerador.randint(3, 8); ox = gerador.randint(6, largura - 10); oy = gerador.randint(6, altura - 10)
        desenho.ellipse([ox - cr, oy - cr, ox + cr, oy + cr], fill=(max(0, c1[0] - 30), max(0, c1[1] - 30), max(0, c1[2] - 30), 200))
    desenho.ellipse([cx - 12, cy - 14, cx - 4, cy - 6], fill=(min(255, c1[0] + 40), min(255, c1[1] + 40), min(255, c1[2] + 30), 120))
    img_pequena = img.resize((largura//2, altura//2), Image.NEAREST)
    return carregar_rgba_gpu(np.array(img_pequena.resize((largura, altura), Image.NEAREST), dtype=np.uint8))

def gerar_planeta(largura=96, altura=96, semente=0) -> int:
    gerador = random.Random(semente)
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); cx = cy = largura // 2; raio = cx - 4
    for y in range(altura):
        for x in range(largura):
            dx, dy = x - cx, y - cy; r = math.sqrt(dx * dx + dy * dy)
            if r <= raio:
                lat = dy / raio
                brilho = 0.7 + 0.3 * math.cos(lat * math.pi * 4)
                cr = int(gerador.randint(100, 180) * brilho)
                cg = int(gerador.randint(60, 130) * brilho)
                cb = int(gerador.randint(30, 80) * brilho)
                img.putpixel((x, y), (cr, cg, cb, 255))
    desenho = ImageDraw.Draw(img)
    desenho.ellipse([cx - raio // 2, cy - raio // 2 - 8, cx, cy - 4], fill=(255, 255, 255, 40))
    if semente % 2 == 0:
        for x in range(largura):
            for yr in range(int(cy - 2), int(cy + 3)):
                if 0 <= yr < altura:
                    dx = abs(x - cx); dy = abs(yr - cy)
                    if raio + 5 < dx < raio + 22:
                        a = int(140 * (1 - dy / 4)) if dy < 4 else 0
                        if a > 0:
                            img.putpixel((x, yr), (220, 190, 120, a))
    img_pequena = img.resize((largura//3, altura//3), Image.NEAREST)
    return carregar_rgba_gpu(np.array(img_pequena.resize((largura, altura), Image.NEAREST), dtype=np.uint8))

def gerar_esfera(cor_r, cor_g, cor_b, largura=24, altura=24) -> int:
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); cx = cy = largura // 2; raio = cx - 2
    for y in range(altura):
        for x in range(largura):
            dx, dy = x - cx, y - cy; r = math.sqrt(dx * dx + dy * dy)
            if r <= raio:
                t = 1 - r / raio; borda = 1 - t * 0.7
                novo_r = int(cor_r * borda * 255); novo_g = int(cor_g * borda * 255); novo_b = int(cor_b * borda * 255)
                img.putpixel((x, y), (min(255, novo_r), min(255, novo_g), min(255, novo_b), 255))
    desenho = ImageDraw.Draw(img)
    desenho.ellipse([cx - raio // 2, cy - raio // 2 - 2, cx - 2, cy - 2], fill=(255, 255, 255, 100))
    img_pequena = img.resize((largura//2, altura//2), Image.NEAREST)
    return carregar_rgba_gpu(np.array(img_pequena.resize((largura, altura), Image.NEAREST), dtype=np.uint8))

def gerar_barra_hud(largura=200, altura=16) -> int:
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); desenho = ImageDraw.Draw(img)
    desenho.rectangle([0, 0, largura - 1, altura - 1], outline=(200, 200, 200, 200), width=2)
    for y in range(2, altura - 2):
        t = y / (altura - 4); c = int(20 + t * 15)
        desenho.line([(2, y), (largura - 2, y)], fill=(c, c, c + 5, 180))
    return carregar_rgba_gpu(np.array(img, dtype=np.uint8))

def gerar_barra_combustivel(largura=196, altura=12, proporcao=1.0) -> int:
    img = Image.new("RGBA", (largura, altura), (0,0,0,0)); desenho = ImageDraw.Draw(img)
    preenchimento = int(largura * proporcao)
    for x in range(preenchimento):
        t = x / max(1, preenchimento)
        if t < 0.5:
            r = int(20 + t * 2 * 200); g = 200; b = 20
        else:
            r = 220; g = int(200 * (1 - (t - 0.5) * 2)); b = 20
        for y in range(altura):
            img.putpixel((x, y), (r, g, b, 220))
    return carregar_rgba_gpu(np.array(img, dtype=np.uint8))

def gerar_digito(digito, largura=14, altura=20) -> int:
    img = Image.new("RGBA", (largura, altura), (0,0,0,0))
    px = img.putpixel
    segmentos = {
        0:[1,0,1,1,1,1,1], 1:[0,0,0,0,1,0,1], 2:[1,1,1,0,1,1,0],
        3:[1,1,1,0,1,0,1], 4:[0,1,0,1,1,0,1], 5:[1,1,1,1,0,0,1],
        6:[1,1,1,1,0,1,1], 7:[1,0,0,0,1,0,1], 8:[1,1,1,1,1,1,1],
        9:[1,1,1,1,1,0,1],
    }
    s = segmentos.get(digito, segmentos[8])
    c = (80, 220, 80, 255)
    if s[0]:
        for x in range(2, largura - 2): px((x, 1), c); px((x, 2), c)
    if s[1]:
        for x in range(2, largura - 2): px((x, altura // 2), c); px((x, altura // 2 + 1), c)
    if s[2]:
        for x in range(2, largura - 2): px((x, altura - 3), c); px((x, altura - 2), c)
    if s[3]:
        for y in range(3, altura // 2): px((1, y), c); px((2, y), c)
    if s[4]:
        for y in range(3, altura // 2): px((largura - 2, y), c); px((largura - 3, y), c)
    if s[5]:
        for y in range(altura // 2 + 2, altura - 3): px((1, y), c); px((2, y), c)
    if s[6]:
        for y in range(altura // 2 + 2, altura - 3): px((largura - 2, y), c); px((largura - 3, y), c)
    return carregar_rgba_gpu(np.array(img, dtype=np.uint8))
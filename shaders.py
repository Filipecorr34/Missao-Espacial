from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GL import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER

VERT_PRINCIPAL = """
#version 330 core
layout(location=0) in vec2 aPos;
layout(location=1) in vec2 aUV;
out vec2 vUV;
uniform mat4 uModelo;
uniform mat4 uProjecao;
uniform vec2 uEscTex;
uniform vec2 uDeslTex;
void main(){
    gl_Position = uProjecao * uModelo * vec4(aPos,0.0,1.0);
    vUV = aUV * uEscTex + uDeslTex;
}
"""

FRAG_PRINCIPAL = """
#version 330 core
in  vec2 vUV;
out vec4 CorFragmento;
uniform sampler2D uTextura;
uniform vec4      uCor;
uniform bool      uUsaTextura;
uniform float     uAlfa;
void main(){
    vec4 corFinal;
    if(uUsaTextura){
        corFinal = texture(uTextura, vUV);
        if(corFinal.a < 0.05) discard;
        corFinal.rgb *= uCor.rgb;
    } else {
        corFinal = uCor;
    }
    corFinal.a *= uAlfa;
    CorFragmento = corFinal;
}
"""

VERT_CEU = """
#version 330 core
layout(location=0) in vec2 aPos;
layout(location=1) in vec2 aUV;
out vec2 vUV;
void main(){ gl_Position = vec4(aPos*2.0,0.0,1.0); vUV=aUV; }
"""

FRAG_CEU = """
#version 330 core
in  vec2 vUV;
out vec4 CorFragmento;
uniform vec3  uCeuTopo;
uniform vec3  uCeuBase;
uniform float uNoite;
uniform float uTempo;
void main(){
    float t = vUV.y;
    vec3 corDia   = mix(uCeuBase, uCeuTopo, t);
    vec3 corNoite = mix(vec3(0.01,0.01,0.07), vec3(0.0,0.0,0.03), t);
    vec3 corFinal = mix(corDia, corNoite, uNoite);
    CorFragmento  = vec4(corFinal, 1.0);
}
"""

def compilar_shaders():
    """Retorna a tupla (prog_principal, prog_ceu) compilados"""
    prog_princ = compileProgram(compileShader(VERT_PRINCIPAL, GL_VERTEX_SHADER), compileShader(FRAG_PRINCIPAL, GL_FRAGMENT_SHADER))
    prog_ceu = compileProgram(compileShader(VERT_CEU, GL_VERTEX_SHADER), compileShader(FRAG_CEU, GL_FRAGMENT_SHADER))
    return prog_princ, prog_ceu
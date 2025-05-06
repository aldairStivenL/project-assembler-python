import re
from encoder import InstructionEncoder

class InstructionParser:
    def __init__(self, instructions_file):
        # Inicializa el encoder con las instrucciones desde el archivo JSON
        self.encoder = InstructionEncoder(instructions_file)
        
        self.abi_to_num = {
            "zero": 0, "ra": 1, "sp": 2, "gp": 3, "tp": 4,
            "t0": 5, "t1": 6, "t2": 7, "s0": 8, "fp": 8, "s1": 9,
            "a0": 10, "a1": 11, "a2": 12, "a3": 13, "a4": 14, "a5": 15,
            "a6": 16, "a7": 17, "s2": 18, "s3": 19, "s4": 20, "s5": 21,
            "s6": 22, "s7": 23, "s8": 24, "s9": 25, "s10": 26, "s11": 27,
            "t3": 28, "t4": 29, "t5": 30, "t6": 31,
            "ft0": 0, "ft1": 1, "ft2": 2, "ft3": 3, "ft4": 4, "ft5": 5, "ft6": 6, "ft7": 7,
            "fs0": 8, "fs1": 9,
            "fa0": 10, "fa1": 11, "fa2": 12, "fa3": 13, "fa4": 14, "fa5": 15, "fa6": 16, "fa7": 17,
            "fs2": 18, "fs3": 19, "fs4": 20, "fs5": 21, "fs6": 22, "fs7": 23, "fs8": 24, "fs9": 25, "fs10": 26, "fs11": 27,
            "ft8": 28, "ft9": 29, "ft10": 30, "ft11": 31
        }


    def parse_register(self, reg):
        if reg in self.abi_to_num:
            return self.abi_to_num[reg]
        elif reg.startswith('x'):
            return int(reg[1:])
        else:
            raise ValueError(f"Registro desconocido: {reg}")
        
    def process_line(self, line):
        # Elimina comentarios y espacios en blanco
        line = line.split("#")[0].strip()
        if not line:  
            return ""  # Devuelve una cadena vacía para líneas ignoradas
        
        # Divide la línea en partes usando comas
        parts = [part.strip() for part in line.split(',')]
        
        # Extrae la instrucción y verifica si es `ecall` o `ebreak`
        instr_and_rd = parts[0].split()
        instr = instr_and_rd[0]

        # 🔹 CASO ESPECIAL: ECALL Y EBREAK (Antes de validar la cantidad de elementos en `instr_and_rd`)
        if instr in ["ecall", "ebreak"]:
            if len(instr_and_rd) != 1:  # Debe ser solo "ecall" o "ebreak"
                raise ValueError(f"❌ ERROR: Formato inválido en la línea '{line}'. Las instrucciones '{instr}' no deben llevar operandos.")

            rd = "x0"  # `ecall` y `ebreak` usan rd=0 (x0)
            rs1 = "x0"  # También rs1=0 (x0)
            imm = "0" if instr == "ecall" else "1"  # `ecall` usa imm=0, `ebreak` usa imm=1

            print(f"📌 Procesando instrucción {instr}: rd={rd}, rs1={rs1}, imm={imm}")

            return self.encoder.encode_i_type(instr, rd, rs1, imm) 

        # 🔹 PROCESO NORMAL PARA OTRAS INSTRUCCIONES (Después de manejar `ecall` y `ebreak`)
        if len(instr_and_rd) != 2:
            raise ValueError(f"❌ ERROR: Formato inválido en la línea '{line}'.")

        instr = instr_and_rd[0]
        rd = instr_and_rd[1]

        try:
            if instr in self.encoder.instructions['r_type_instructions']:
                if len(parts) < 3:
                    raise ValueError(f"Formato inválido: {line}")
                rs1 = parts[1].strip()
                rs2 = parts[2].strip()
                return self.encoder.encode_r_type(instr, rd, rs1, rs2)

            elif instr in self.encoder.instructions['i_type_instructions']:
                                   #CASO ESPECIAL
                ##################################################################################################################
                if instr == "jalr":
                    # Expresión regular para manejar el formato '100(x2)'
                    match = re.match(r"(-?\d+)\s*\(\s*(\w+)\s*\)", parts[1])
                    if not match:
                        raise ValueError(f"❌ ERROR: Sintaxis inválida en '{line}'. Formato esperado: 'jalr rd, offset(rs1)'.")

                    offset, rs1 = match.groups()  # Extrae el inmediato y rs1
                    print(f"📌 Procesando instrucción JALR: instr={instr}, rd={rd}, rs1={rs1}, imm={offset}")

                    return self.encoder.encode_i_type(instr, rd, rs1, offset)
                #####################################################################################################################           
                elif len(parts) < 3:
                    raise ValueError(f"Formato inválido: {line}")
                rs1 = parts[1].strip()
                imm = parts[2].strip()
                return self.encoder.encode_i_type(instr, rd, rs1, imm)

            elif instr in self.encoder.instructions['i_type_load_instructions']:
                if len(parts) < 2:
                    raise ValueError(f"Formato inválido: {line}")
                
                # Expresión regular para manejar el formato '100(x2)'
                match = re.match(r"(-?\d+)\s*\(\s*(\w+)\s*\)", parts[1])
                if not match:
                    raise ValueError(f"Formato inválido para instrucción de carga: {line}")
                offset, rs1 = match.groups()
                return self.encoder.encode_i_type_load(instr, rd, rs1, offset)

            elif instr in self.encoder.instructions['s_type_instructions']:
                if len(parts) < 2:
                    raise ValueError(f"Formato inválido: {line}")
                match = re.match(r"(-?\d+)\s*\(\s*(\w+)\s*\)", parts[1])
                if not match:
                    raise ValueError(f"Formato inválido para instrucción de almacenamiento: {line}")
                offset, rs1 = match.groups()
                return self.encoder.encode_s_type(instr, rs1, rd, offset)

            elif instr in self.encoder.instructions['b_type_instructions']:
                if len(parts) < 3:
                    raise ValueError(f"Formato inválido: {line}")
                rs1 = parts[1].strip()
                imm = parts[2].strip()
                print("IMEDIATO")
                print(imm)
                return self.encoder.encode_b_type(instr, rd, rs1, imm)

            elif instr in self.encoder.instructions['j_type_instructions']:
                if len(parts) != 2:
                    raise ValueError(f"❌ ERROR: Formato inválido en la línea '{line}'. Debe ser 'jal rd, imm'.")
                
                imm = parts[1].strip()

                print(f"📌 Procesando instrucción tipo J: {instr}, rd={rd}, imm={imm}")

                return self.encoder.encode_j_type(instr, rd, imm)




            elif instr in self.encoder.instructions['u_type_instructions']:
                if len(parts) < 2:
                    raise ValueError(f"Formato inválido: {line}")
                imm = parts[1].strip()
                return self.encoder.encode_u_type(instr, rd, imm)

            else:
                raise ValueError(f"Instrucción desconocida: {instr}")
        
        except Exception as e:
            raise ValueError(f"Error al procesar la línea '{line}': {e}")

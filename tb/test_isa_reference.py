"""Independent RV32I instruction interpreter and architectural-state comparison.

Scope: the project's 37 instructions, naturally aligned zero-wait data memory,
no traps/CSRs/interrupts, single hart. No ISA compliance or timing claim.
No imports from existing project test helpers. FENCE cases only check the
existing strongly ordered memory model, without external observers or MMIO.
"""
import collections
import json
import os
from pathlib import Path
import random
import cocotb
from cocotb.triggers import Timer

MASK = (1 << 32) - 1

def signed(x, width=32):
    return (x & ((1 << (width - 1)) - 1)) - (x & (1 << (width - 1)))

def encode_r(f3, f7, rd, a, b):
    return f7 << 25 | b << 20 | a << 15 | f3 << 12 | rd << 7 | 0x33

def encode_i(op, f3, rd, a, imm):
    return (imm & 0xfff) << 20 | a << 15 | f3 << 12 | rd << 7 | op

def encode_store(f3, a, b, imm):
    return (imm & 0xfe0) << 20 | b << 20 | a << 15 | f3 << 12 | (imm & 31) << 7 | 0x23

def encode_branch(f3, a, b, imm):
    return ((imm >> 12) & 1) << 31 | ((imm >> 5) & 63) << 25 | b << 20 | a << 15 | f3 << 12 | ((imm >> 1) & 15) << 8 | ((imm >> 11) & 1) << 7 | 0x63

def encode_jal(rd, imm):
    return ((imm >> 20) & 1) << 31 | ((imm >> 1) & 1023) << 21 | ((imm >> 11) & 1) << 20 | ((imm >> 12) & 255) << 12 | rd << 7 | 0x6f

def model(words, initial_memory, terminal):
    """Decode raw instruction words, no use of generator operation metadata."""
    regs = [0] * 32
    known = {0}
    memory = dict(initial_memory)
    pc = 0
    rows, stores = [], []
    counts = collections.Counter()
    for _ in range(20000):
        assert pc in words, f'reference PC outside program: {pc:x}'
        inst = words[pc]
        op, rd, f3 = inst & 127, (inst >> 7) & 31, (inst >> 12) & 7
        a, b, f7 = (inst >> 15) & 31, (inst >> 20) & 31, inst >> 25
        x, y = regs[a], regs[b]
        imm = signed(inst >> 20, 12)
        next_pc, result, label = (pc + 4) & MASK, None, None
        if op == 0x33:
            key = f3, f7
            ops = {(0,0):('add',lambda:x+y), (0,32):('sub',lambda:x-y),
                (1,0):('sll',lambda:x << (y&31)), (2,0):('slt',lambda:int(signed(x)<signed(y))),
                (3,0):('sltu',lambda:int(x<y)), (4,0):('xor',lambda:x^y),
                (5,0):('srl',lambda:x >> (y&31)), (5,32):('sra',lambda:signed(x) >> (y&31)),
                (6,0):('or',lambda:x|y), (7,0):('and',lambda:x&y)}
            label, calc = ops[key]
            result = calc()
        elif op == 0x13:
            if f3 == 0: label, result = 'addi', x + imm
            elif f3 == 2: label, result = 'slti', int(signed(x) < imm)
            elif f3 == 3: label, result = 'sltiu', int(x < (imm & MASK))
            elif f3 == 4: label, result = 'xori', x ^ (imm & MASK)
            elif f3 == 6: label, result = 'ori', x | (imm & MASK)
            elif f3 == 7: label, result = 'andi', x & (imm & MASK)
            elif f3 == 1 and f7 == 0: label, result = 'slli', x << b
            elif f3 == 5 and f7 == 0: label, result = 'srli', x >> b
            elif f3 == 5 and f7 == 32: label, result = 'srai', signed(x) >> b
            else: raise AssertionError(f'illegal reference shift {inst:08x}')
        elif op in (0x03, 0x23):
            if op == 0x23: imm = signed(((inst >> 25) << 5) | ((inst >> 7) & 31), 12)
            address = (x + imm) & MASK
            size = 1 << (f3 & 3)
            assert address % size == 0, f'misaligned reference access: {address:x}/{size}'
            if op == 0x03:
                label = {0:'lb',1:'lh',2:'lw',4:'lbu',5:'lhu'}[f3]
                result = sum(memory.get((address+k)&MASK,0) << (k*8) for k in range(size))
                if f3 in (0,1): result = signed(result, size*8)
            else:
                label = {0:'sb',1:'sh',2:'sw'}[f3]
                for k in range(size): memory[(address+k)&MASK] = (y >> (k*8)) & 255
                stores.append((address & ~3, ((1 << size)-1) << (address&3), (y << ((address&3)*8)) & MASK))
        elif op == 0x63:
            offset = signed(((inst>>31)&1)<<12 | ((inst>>7)&1)<<11 | ((inst>>25)&63)<<5 | ((inst>>8)&15)<<1, 13)
            label, take = {0:('beq',x==y),1:('bne',x!=y),4:('blt',signed(x)<signed(y)),
                5:('bge',signed(x)>=signed(y)),6:('bltu',x<y),7:('bgeu',x>=y)}[f3]
            if take: next_pc = (pc + offset) & MASK
        elif op == 0x37: label, result = 'lui', inst & 0xfffff000
        elif op == 0x17: label, result = 'auipc', pc + (inst & 0xfffff000)
        elif op == 0x6f:
            offset = signed(((inst>>31)&1)<<20 | ((inst>>12)&255)<<12 | ((inst>>20)&1)<<11 | ((inst>>21)&1023)<<1, 21)
            label, result, next_pc = 'jal', pc + 4, (pc + offset) & MASK
        elif op == 0x67 and f3 == 0:
            label, result, next_pc = 'jalr', pc + 4, (x + imm) & MASK & ~1
        elif op == 0x0f and f3 == 0:
            # Ordering already follows program order in this EEI. This does not
            # model a cache, bus, MMIO ordering, other hart, or FENCE.I.
            label = 'fence'
        else: raise AssertionError(f'unsupported instruction {inst:08x}')
        if result is not None and rd:
            regs[rd] = result & MASK
            known.add(rd)
        counts[label] += 1
        rows.append((pc, tuple(regs), frozenset(known)))
        if pc == terminal: return rows, stores, memory, counts
        pc = next_pc
    raise AssertionError('reference program did not terminate')

def program(seed, count=256):
    rng = random.Random(seed)
    instructions = []
    # Initialise every nonzero register through the public instruction port.
    for rd in range(1,32):
        value = rng.getrandbits(32)
        instructions += [(value & 0xfffff000) | rd<<7 | 0x37, encode_i(0x13,0,rd,rd,value&0x7ff)]
    instructions += [encode_i(0x13,0,31,0,0x700)]
    r_ops = [(0,0),(0,32),(1,0),(2,0),(3,0),(4,0),(5,0),(5,32),(6,0),(7,0)]
    for n in range(count):
        rd, a, b = rng.randrange(31), rng.randrange(32), rng.randrange(32)
        kind = rng.randrange(9)
        if kind == 0:
            f3,f7 = rng.choice(r_ops); instructions.append(encode_r(f3,f7,rd,a,b))
        elif kind == 1:
            f3 = rng.choice([0,2,3,4,6,7]); instructions.append(encode_i(0x13,f3,rd,a,rng.randrange(-2048,2048)))
        elif kind == 2:
            f3,f7 = rng.choice([(1,0),(5,0),(5,32)]); instructions.append(encode_i(0x13,f3,rd,a,(f7<<5)|rng.randrange(32)))
        elif kind == 3:
            f3 = rng.choice([0,1,2,4,5]); width=1<<(f3&3)
            instructions.append(encode_i(0x03,f3,rd,31,rng.randrange(-64,64)//width*width))
        elif kind == 4:
            f3 = rng.randrange(3); width=1<<f3
            instructions.append(encode_store(f3,31,b,rng.randrange(-64,64)//width*width))
        elif kind == 5:
            instructions.append(encode_branch(rng.choice([0,1,4,5,6,7]),a,b,8))
        elif kind == 6:
            instructions.append((rng.getrandbits(20)<<12) | rd<<7 | rng.choice([0x17,0x37]))
        elif kind == 7:
            instructions.append(encode_jal(rd,8))
        else:
            # Aliased rd=rs1 catches using a just-written link as the target.
            # Two landing pads prevent a previous +8 branch from skipping
            # the JALR address setup and using an arbitrary stale register.
            instructions += [encode_i(0x13,0,0,0,0)]*2
            here = len(instructions)*4
            instructions += [encode_i(0x13,0,30,0,here+13), encode_i(0x67,0,30,30,0), encode_i(0x13,0,0,0,0)]
    # Padding makes a last forward skip land inside the program.
    instructions += [encode_i(0x13,0,0,0,0)]*4
    words = {i*4:v for i,v in enumerate(instructions)}
    memory = {addr:rng.randrange(256) for addr in range(0x680,0x780)}
    return words,memory,(len(instructions)-1)*4

def fence_program():
    instructions = [encode_i(0x13,0,31,0,0x700), encode_i(0x13,0,1,0,-1)]
    for pred in range(16):
        for succ in range(16):
            instructions += [encode_store(2,31,1,0), pred<<24 | succ<<20 | 0x0f,
                encode_i(0x03,2,2,31,0), encode_i(0x13,0,1,2,-1)]
    instructions += [encode_i(0x13,0,0,0,0)]
    return {i*4:v for i,v in enumerate(instructions)}, {}, (len(instructions)-1)*4

async def check(dut, case, words, initial, terminal):
    rows, wanted_stores, wanted_memory, counts = model(words,initial,terminal)
    pipeline = hasattr(dut,'retire_valid')
    rf = dut.u_id.u_register_file if pipeline else dut.u_register_file
    dut.clk.value=0; dut.reset.value=1; dut.instr.value=0; dut.data_read_data.value=0
    await Timer(1,unit='ns'); dut.clk.value=1; await Timer(1,unit='ns')
    dut.clk.value=0; dut.reset.value=0
    memory, stores, retired = dict(initial), [], 0
    for cycle in range(len(rows)*5+30):
        pc=int(dut.current_pc.value)
        dut.instr.value=words.get(pc,0x13)
        await Timer(1,unit='ns')
        address=int(dut.data_addr.value)
        dut.data_read_data.value=sum(memory.get((address&~3)+k,0)<<(k*8) for k in range(4))
        await Timer(1,unit='ns')
        event=None
        if int(dut.data_write_en.value):
            event=(int(dut.data_addr.value)&~3, int(dut.data_write_strb.value), int(dut.data_write_data.value))
        valid=bool(int(dut.retire_valid.value)) if pipeline else True
        retired_pc=int(dut.retire_pc.value) if pipeline else pc
        dut.clk.value=1; await Timer(1,unit='ns')
        if event is not None:
            # Unselected store-data lanes are not architectural state.
            mask=sum(255<<(8*k) for k in range(4) if event[1] & (1<<k))
            item=(event[0],event[1],event[2]&mask)
            assert len(stores)<len(wanted_stores), f'{case}: unexpected store {item}'
            expected=wanted_stores[len(stores)]; expected=(expected[0],expected[1],expected[2]&mask)
            assert item==expected, f'{case}: store {len(stores)} {item} != {expected}'
            stores.append(item)
            for k in range(4):
                if event[1] & (1<<k): memory[event[0]+k]=(event[2]>>(8*k))&255
        if valid:
            assert retired<len(rows), f'{case}: unexpected extra retirement'
            wanted_pc,regs,known=rows[retired]
            assert retired_pc==wanted_pc, f'{case}: retirement {retired} PC {retired_pc:x} != {wanted_pc:x}'
            for index in known-{0}:
                actual=int(rf.registers[index].value)
                assert actual==regs[index], f'{case}: retire {retired} PC {wanted_pc:x} inst {words[wanted_pc]:08x} x{index} {actual:08x} != {regs[index]:08x}'
            retired+=1
            if retired==len(rows):
                assert len(stores)==len(wanted_stores), f'{case}: missing stores'
                assert memory==wanted_memory, f'{case}: final byte memory differs'
                return {'case':case,'retired':retired,'stores':len(stores),'cycles':cycle+1,'instructions':dict(counts)}
        dut.clk.value=0; await Timer(1,unit='ns')
    raise AssertionError(f'{case}: timeout after {retired}/{len(rows)} retirements')

def save(dut,name,results):
    totals=collections.Counter()
    for result in results: totals.update(result['instructions'])
    out=Path(os.environ.get('ISA_RESULTS_DIR','.'))
    out.mkdir(parents=True,exist_ok=True)
    top='pipeline' if hasattr(dut,'retire_valid') else 'single'
    data={'core':top,'name':name,'programs':len(results),'retired':sum(r['retired'] for r in results),
        'stores':sum(r['stores'] for r in results),'instruction_counts':dict(sorted(totals.items())),
        'scope':'Naturally aligned zero-wait memory; no exceptions, CSRs, interrupts, caches or MMIO; custom interpreter, not an external ISS compliance suite.',
        'results':results}
    (out/f'{top}_{name}.json').write_text(json.dumps(data,indent=2)+'\n')
    dut._log.info('INDEPENDENT_ISA %s programs=%d retired=%d stores=%d instruction_kinds=%d',top,data['programs'],data['retired'],data['stores'],len(totals))

@cocotb.test()
async def independent_machine_code_programs(dut):
    results=[]
    for seed in range(64):
        results.append(await check(dut,f'seed_{seed}',*program(seed)))
    save(dut,'random',results)
    covered={name for row in results for name in row['instructions']}
    assert len(covered)==37, f'missing existing supported instructions: {sorted(covered)}'

@cocotb.test()
async def fence_in_strongly_ordered_memory_model(dut):
    save(dut,'fence',[await check(dut,'fence_all_predecessor_successor_masks',*fence_program())])

# Catálogo de ações — AMS

O agente não trabalha diretamente nas máquinas: consulta informações e interage sempre com humanos, como técnicos e supervisores. Quem age sobre a máquina são eles.

| Ação | Entrada | Saída | É reversível? | Risco se errar |
|---|---|---|---|---|
| Consultar a ordem de serviço | Número da ordem | Máquina, tipo de produto, leituras e descrição da intervenção | Sim: só lê | Texto com ruído ou leitura errada contamina o risco e as NRs indicadas, e o técnico recebe uma recomendação sem base |
| Consultar o histórico de recomendações | Identificador da máquina | Recomendações anteriores, se foram executadas e falhas registradas | Sim: só lê | Histórico incompleto faz o agente mudar de recomendação sem motivo ou ignorar falhas recentes da mesma máquina |
| Buscar o trecho aplicável das NRs | Descrição da intervenção e NRs candidatas (10, 12 e 35) | Trechos com norma e item citados | Sim: só lê | Trecho errado omite uma exigência de segurança, como a sequência de desenergização da NR-10, ou cita um item que não se aplica |
| Avaliar o risco de falha | Leituras e histórico da máquina | Nível de risco, modo de falha provável e justificativa | Sim: só calcula e não tem efeito externo | Falso negativo deixa a máquina falhar sem aviso, com reparo e espera de peças; falso positivo para a máquina sem necessidade e tira horas de produção |
| Montar o roteiro de segurança | Descrição da intervenção e trechos das NRs | Itens a conferir em ordem, pendências e indicação de bloqueio e etiquetagem | Sim: é rascunho até ser enviado | Roteiro que omite o bloqueio ou inverte a sequência da NR-10 expõe o técnico a energia na intervenção |
| Recomendar a ação ao técnico | Ordem de serviço, risco avaliado, roteiro completo com NRs citadas e justificativa | Recomendação enviada: parar, inspecionar ou seguir, com NRs e bloqueio | Não: a mensagem pode ser corrigida, mas o que o técnico já fez a partir dela não se desfaz | Comunicação, risco alto: recomendar "seguir" ou omitir o bloqueio leva o técnico a intervir em uma máquina energizada ou prestes a falhar; mudar de recomendação sem motivo desgasta a confiança dele |
| Escalar ao supervisor | Ordem de serviço, motivo (dado inconsistente ou baixa confiança) e o que já foi conferido | Caso na fila do supervisor de segurança | Sim: o caso pode voltar ao fluxo normal | Comunicação: escalar demais cansa o supervisor e atrasa ordens; escalar sem o que já foi conferido duplica o trabalho; não escalar deixa um dado inconsistente virar recomendação errada |
| Registrar a recomendação para auditoria | Ordem de serviço, recomendação, justificativa e fontes usadas | Registro com data e hora | Parcialmente: o registro permanece, e a correção entra como novo registro | Escrita: registro ausente ou errado impede apurar um incidente e mostrar que a norma foi seguida |

**Quem executa cada ação:**

- **O agente sozinho:** consultar a ordem de serviço, consultar o histórico, buscar nas NRs, avaliar o risco, redigir o roteiro, escalar ao supervisor e registrar para auditoria. Nenhuma dessas ações atua sobre a máquina.
- **Com confirmação humana:** recomendar ao técnico. O agente envia a recomendação e o roteiro, mas nada acontece até o técnico decidir segui-los e conferir cada item no posto.
- **Só humano:** aplicar e retirar o bloqueio, parar e religar a máquina, executar a intervenção e liberá-la.

**O que o agente JAMAIS executa sozinho:** o agente não atua sobre o mundo físico. Ele nunca:

- libera a intervenção;
- aplica ou retira bloqueio e etiquetagem;
- para, liga ou religa uma máquina;
- opera a máquina ou executa a intervenção;
- substitui a decisão do técnico ou do supervisor.

A liberação é a ação crítica: ela só pode acontecer com todos os itens conferidos e nenhuma pendência aberta, e cabe a um humano autorizado. Se o agente errar, o técnico pode intervir em uma máquina energizada, e o efeito de um acidente não se desfaz. Por isso, essas ações ficam fora deste catálogo.

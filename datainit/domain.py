def gen_domain(config):
    domain_config = config.domain_config
    name = domain_config['name']
    interval = domain_config['interval']
    path = domain_config['domain_path']
    str1 = f'''
    (define (domain {name})
    (:requirements :typing :fluents :CONDITIONAL-EFFECTS :equality :durative-actions :negative-preconditions)
    (:types
        pole slot product - object
    )
    (:predicates

        (pole_position ?p - pole ?s - slot) ;pole ?p is at slot ?s
        (slot_have_pole ?s - slot)

        (pole_region ?p - pole ?s - slot) ;pole ?p is available to be at ?s
        (pole_have_things ?p - pole ?r - product) ;pole is hanging ?r
        (pole_empty ?p - pole) ;pole has nothing

        (pole_available ?p - pole)

        (product_at ?r - product ?s - slot)
        ; (product_craft ?r - product ?c - craft)
        (target_slot ?s - slot ?r - product)
        (gear_pole ?p - pole)

        (forward_slot_connection ?s1 - slot ?s2 - slot)
        (inverse_slot_connection ?s1 - slot ?s2 - slot)
        (exchanging_connection ?s1 - slot ?s2 - slot)
        (border_slot ?s - slot)

        ;(slot_setting ?s - slot ?o - process)
        (stocking_slot ?s - slot)
        (blanking_slot ?s - slot)
        (exchanging_slot ?s - slot)

        (slot_not_available ?s - slot)
        ;  (complete ?r - product)

        (pole_start_moving ?p - pole)
        (pole_stop_moving ?p - pole)

    )

    (:functions
        (procedure_executing ?r - product) ;How many procedures are executed?
        ;(procedure_craft ?o - process ?c - craft)
        ;(procedure_blanking ?c - craft)

        (pole_moving_duration_each_slot)
        (pole_stop_duration)
        (pole_start_duration)
        (pole_hangon_duration)
        (pole_hangoff_duration)
        (gear_moving_duration)

        ;(procedure_duration ?o - process ?c - craft)
    )

    ;;;;;;;;;;;;;;;;;;;  Actions About Poles ;;;;;;;;;;;;;;;;;;;;;;

    (:durative-action Start-Moving-Pole
        :parameters (?p - pole)
        :duration (= ?duration (pole_start_duration))
        :condition ( and (at start (pole_stop_moving ?p))
            (at start(pole_available ?p))
        )
        :effect (and (at end (pole_start_moving ?p))
            (at start (not (pole_stop_moving ?p)))
            (at start (not (pole_available ?p)))
            (at end (pole_available ?p))
        )
    )
    '''
    str2 = gen_move(interval)
    str3 = '''(:durative-action HangUp-Pole
        :parameters (?p - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangon_duration))
        :condition (and (at start(pole_empty ?p))
            ;(at start(product_available ?r))
            (at start(product_at ?r ?s))
            (over all(pole_position ?p ?s))
            (at start (pole_available ?p))
            (at start(slot_not_available ?s))
            (over all(not(stocking_slot ?s)))
            (over all(not(exchanging_slot ?s)))
        )
        :effect (and (at start(not (pole_empty ?p)))
            ;(at start(not (product_available ?r)))
            (at start (not (product_at ?r ?s)))
            (at end (pole_have_things ?p ?r))
            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))
            (at end(not (slot_not_available ?s)))
        )
    )

    (:durative-action HangUp-Pole-exchanging
        :parameters (?p - pole ?g - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangon_duration))
        :condition (and (at start(pole_empty ?p))
            (at start(not (pole_empty ?g)))

            ;(at start(product_available ?r))
            (at start(product_at ?r ?s))
            (over all(pole_position ?p ?s))
            (over all(pole_position ?g ?s))

            (at start (pole_available ?p))
            (at start (pole_available ?g))

            (at start(slot_not_available ?s))

            (over all(not(stocking_slot ?s)))
            (over all(exchanging_slot ?s))

            (over all (not (gear_pole ?p)))
        )
        :effect (and (at start(not (pole_empty ?p)))
            (at end (pole_empty ?g))

            (at start (not (product_at ?r ?s)))

            (at end (pole_have_things ?p ?r))
            (at start (not (pole_have_things ?g ?r)))

            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))

            (at start(not (pole_available ?g)))
            (at end(pole_available ?g))

            (at end(not (slot_not_available ?s)))
        )
    )

    (:durative-action HangUp-Pole-stocking
        :parameters (?p - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangon_duration))
        :condition (and (at start(pole_empty ?p))
            ;(at start(product_available ?r))
            (at start(product_at ?r ?s))
            (over all(pole_position ?p ?s))
            (at start (pole_available ?p))
            (over all(stocking_slot ?s))
        )
        :effect (and (at start(not (pole_empty ?p)))
            ;(at start(not (product_available ?r)))
            (at start (not (product_at ?r ?s)))
            (at end (pole_have_things ?p ?r))
            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))
        )
    )

    (:durative-action HangOff-Pole
        :parameters (?p - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangoff_duration))
        :condition (and (at start(pole_have_things ?p ?r))
            (over all(pole_position ?p ?s))
            (at start (pole_available ?p))
            (over all (target_slot ?s ?r))
            (at start (not (slot_not_available ?s)))
            (over all (not (blanking_slot ?s)))
            (over all (not (exchanging_slot ?s)))
        )
        :effect (and (at end(pole_empty ?p))
            (at end(product_at ?r ?s))
            (at end(not (pole_have_things ?p ?r)))
            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))
            (at end(not (target_slot ?s ?r)))
            (at start (slot_not_available ?s))
        )
    )

    (:durative-action HangOff-Pole-blanking
        :parameters (?p - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangoff_duration))
        :condition (and (at start(pole_have_things ?p ?r))
            (over all(pole_position ?p ?s))
            (at start (pole_available ?p))
            (over all (target_slot ?s ?r))
            (over all (blanking_slot ?s))
        )
        :effect (and (at end(pole_empty ?p))
            (at end(product_at ?r ?s))
            (at end(not (pole_have_things ?p ?r)))
            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))
            (at end(not (target_slot ?s ?r)))
        )
    )

    (:durative-action HangOff-Pole-exchanging
        :parameters (?p - pole ?g - pole ?s - slot ?r - product)
        :duration (= ?duration (pole_hangoff_duration))
        :condition (and (at start(pole_have_things ?p ?r))

            (over all(pole_position ?p ?s))
            (over all(pole_position ?g ?s))

            (at start (pole_available ?p))
            (at start (pole_available ?g))

            (over all (target_slot ?s ?r))
            (at start (not (slot_not_available ?s)))
            (over all (exchanging_slot ?s))

            (over all (not (gear_pole ?p)))
        )
        :effect (and (at end(pole_empty ?p))
            (at end(not (pole_empty ?g)))

            (at end(product_at ?r ?s))
            (at start (slot_not_available ?s))

            (at end(not (pole_have_things ?p ?r)))
            (at end(pole_have_things ?g ?r))

            (at start(not (pole_available ?p)))
            (at end(pole_available ?p))

            (at start(not (pole_available ?g)))
            (at end(pole_available ?g))

            (at end(not (target_slot ?s ?r)))
        )
    )
    )'''
    domain = str1 + str2 + str3
    with open(path, 'w') as f:
        print(domain, file = f)

def gen_move(interval):
    res = ''
    for direct in ['forward', 'inverse']:
        for i in range(interval + 1):
            parameters = ''
            forward_connection = ''
            con_not_slot_have_pole = ''
            eff_not_slot_have_pole = ''
            slot_have_pole = ''
            border_slot = ''
            if i > 0:
                border_slot = f'(over all(border_slot ?s{interval + 2 - i}))\n'
            for j in range(interval - i + 2):
                parameters += f'?s{j + 1} - slot '
                slot_have_pole += f'(at start (slot_have_pole ?s{j + 1}))'
                if j != 1:
                    eff_not_slot_have_pole += f'(at end (not (slot_have_pole ?s{j + 1})))\n'
            
            for j in range(interval + 1 -i):
                forward_connection += f'(over all ({direct}_slot_connection ?s{j + 1} ?s{j + 2}))\n'
                con_not_slot_have_pole += f'(over all (not (slot_have_pole ?s{j + 2})))\n'

            
        
            str = f'''
                (:durative-action Move-Pole-{direct}-{i + 1}
                :parameters (?p - pole {parameters})
                :duration (= ?duration (pole_moving_duration_each_slot))
                :condition (and
                    {border_slot}
                    (over all (pole_start_moving ?p))
                    (at start (pole_position ?p ?s1))
                    (at start (pole_available ?p))
                    (over all (pole_region ?p ?s1))
                    (over all (pole_region ?p ?s2))
                    {forward_connection}
                    (at start (slot_have_pole ?s1))
                    {con_not_slot_have_pole}
                )
                :effect (and
                    (at start(not (pole_position ?p ?s1)))
                    (at end(pole_position ?p ?s2))
                    {slot_have_pole}
                    {eff_not_slot_have_pole}
                    (at end(slot_have_pole ?s2))
                    (at start(not (pole_available ?p)))
                    (at end(pole_available ?p))
                )
            )
            '''

            res += str
    
    return res

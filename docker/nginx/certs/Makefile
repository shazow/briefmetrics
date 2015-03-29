%:
	mkdir $@; cd $@; cfssl selfsign $@ ../csr.json | cfssljson -bare selfsigned
	mv $@/selfsigned.pem $@.crt; mv $@/selfsigned-key.pem $@.key
